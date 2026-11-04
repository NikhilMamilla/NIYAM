import json
import sqlite3
from pathlib import Path

import yaml

from app.corpus.models import Clause

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "corpus.db"
COLUMNS = list(Clause.model_fields)


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
