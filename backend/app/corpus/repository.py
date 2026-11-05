import json
import sqlite3
from pathlib import Path

import yaml

from app.corpus.models import Clause, RuleUnit

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "corpus.db"
COLUMNS = list(Clause.model_fields)
UNIT_COLUMNS = list(RuleUnit.model_fields)


def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS clauses (
            id TEXT PRIMARY KEY, source_doc TEXT NOT NULL, clause_number TEXT NOT NULL,
            title TEXT, text TEXT NOT NULL, page INTEGER NOT NULL, section_path TEXT NOT NULL,
            tier TEXT NOT NULL, topic TEXT, status TEXT NOT NULL, notes TEXT)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS rule_units (
            id TEXT PRIMARY KEY, clause_id TEXT NOT NULL REFERENCES clauses(id), text TEXT NOT NULL,
            tier TEXT NOT NULL, status TEXT NOT NULL, expected_artifact TEXT,
            human_reviewed INTEGER NOT NULL, reviewer TEXT, notes TEXT, reviewed_on TEXT)"""
    )
    columns = {r[1] for r in conn.execute("PRAGMA table_info(rule_units)")}
    for column in ("reviewed_on", "duplicate_of"):  # databases created before these fields existed
        if column not in columns:
            conn.execute(f"ALTER TABLE rule_units ADD COLUMN {column} TEXT")
    conn.commit()


def upsert_clause(conn: sqlite3.Connection, clause: Clause) -> None:
    row = clause.model_dump()
    row["section_path"] = json.dumps(row["section_path"])
    placeholders = ", ".join("?" for _ in COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in COLUMNS if c != "id")
    conn.execute(
        f"INSERT INTO clauses ({', '.join(COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}",
        [row[c] for c in COLUMNS],
    )
    conn.commit()


def _to_clause(row: sqlite3.Row) -> Clause:
    data = dict(row)
    data["section_path"] = json.loads(data["section_path"])
    return Clause(**data)


def get_clause(conn: sqlite3.Connection, clause_id: str) -> Clause | None:
    row = conn.execute("SELECT * FROM clauses WHERE id = ?", (clause_id,)).fetchone()
    return _to_clause(row) if row else None


def list_clauses(
    conn: sqlite3.Connection,
    tier: str | None = None,
    status: str | None = None,
    topic: str | None = None,
    search: str | None = None,
) -> list[Clause]:
    where, args = [], []
    for col, val in (("tier", tier), ("status", status), ("topic", topic)):
        if val is not None:
            where.append(f"{col} = ?")
            args.append(val)
    if search:
        where.append("(text LIKE ? OR title LIKE ?)")
        args += [f"%{search}%"] * 2
    sql = "SELECT * FROM clauses" + (" WHERE " + " AND ".join(where) if where else "")
    rows = conn.execute(sql + " ORDER BY page, id", args).fetchall()
    return [_to_clause(r) for r in rows]


def count(conn: sqlite3.Connection, by: str | None = None) -> int | dict:
    if by is None:
        return conn.execute("SELECT COUNT(*) FROM clauses").fetchone()[0]
    if by not in ("tier", "status", "topic"):
        raise ValueError(f"cannot group by {by!r}")
    rows = conn.execute(f"SELECT {by}, COUNT(*) FROM clauses GROUP BY {by}").fetchall()
    return {r[0]: r[1] for r in rows}


def export_selected(conn: sqlite3.Connection, path: Path) -> int:
    clauses = list_clauses(conn, status="selected")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump([c.model_dump() for c in clauses], fh, allow_unicode=True, sort_keys=False, width=100)
    return len(clauses)


def import_selected(conn: sqlite3.Connection, path: Path) -> int:
    with open(path, encoding="utf-8") as fh:
        items = yaml.safe_load(fh) or []
    for item in items:
        upsert_clause(conn, Clause(**item))
    return len(items)


def _squash(text: str) -> str:
    return " ".join(text.split())


def upsert_unit(conn: sqlite3.Connection, unit: RuleUnit) -> None:
    clause = get_clause(conn, unit.clause_id)
    if clause is None:
        raise ValueError(f"no clause {unit.clause_id}")
    # Only whitespace is normalised: PDF line breaks are layout, not wording.
    if _squash(unit.text) not in _squash(clause.text):
        raise ValueError(f"unit text is not a verbatim substring of {unit.clause_id}: {unit.text!r}")
    placeholders = ", ".join("?" for _ in UNIT_COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in UNIT_COLUMNS if c != "id")
    row = unit.model_dump()
    conn.execute(
        f"INSERT INTO rule_units ({', '.join(UNIT_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}",
        [row[c] for c in UNIT_COLUMNS],
    )
    conn.commit()


def get_unit(conn: sqlite3.Connection, unit_id: str) -> RuleUnit | None:
    row = conn.execute("SELECT * FROM rule_units WHERE id = ?", (unit_id,)).fetchone()
    return RuleUnit(**dict(row)) if row else None


def list_units(conn: sqlite3.Connection, status: str | None = None) -> list[RuleUnit]:
    sql, args = "SELECT * FROM rule_units", []
    if status is not None:
        sql, args = sql + " WHERE status = ?", [status]
    return [RuleUnit(**dict(r)) for r in conn.execute(sql + " ORDER BY id", args).fetchall()]


def export_units(conn: sqlite3.Connection, path: Path) -> int:
    units = list_units(conn)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump([u.model_dump() for u in units], fh, allow_unicode=True, sort_keys=False, width=100)
    return len(units)


def import_units(conn: sqlite3.Connection, path: Path) -> int:
    with open(path, encoding="utf-8") as fh:
        items = yaml.safe_load(fh) or []
    for item in items:
        upsert_unit(conn, RuleUnit(**item))
    return len(items)
