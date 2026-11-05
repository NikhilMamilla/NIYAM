import argparse
import sys
from pathlib import Path
from typing import get_args

from app.corpus import repository as repo
from app.corpus.extract_mbbl import extract_pages, segment
from app.corpus.models import Clause, RuleUnit, Status, Tier
from app.corpus.suggest import MAX_REVIEWABLE_CHARS, render_markdown, suggest
from app.corpus import review

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PDF = REPO_ROOT / "rules" / "source" / "mbbl-2016.pdf"
DEFAULT_YAML = REPO_ROOT / "rules" / "corpus" / "mbbl-2016.selected.yaml"
DEFAULT_CANDIDATES = REPO_ROOT / "docs" / "corpus-candidates.md"
DEFAULT_UNITS_YAML = REPO_ROOT / "rules" / "corpus" / "rule-units.yaml"
CURATED_FIELDS = ("tier", "topic", "status", "notes")


def cmd_ingest(conn, args):
    if not args.pdf.exists():
        sys.exit(f"PDF not found: {args.pdf} (see rules/source/README.md)")
    clauses = segment(extract_pages(args.pdf))
    for clause in clauses:
        existing = repo.get_clause(conn, clause.id)
        if existing:  # re-ingest refreshes source text but keeps human curation
            clause = clause.model_copy(update={f: getattr(existing, f) for f in CURATED_FIELDS})
        repo.upsert_clause(conn, clause)
    print(f"ingested {len(clauses)} clauses from {args.pdf.name}; db now holds {repo.count(conn)}")


def cmd_stats(conn, args):
    print(f"total: {repo.count(conn)}")
    for field in ("tier", "status", "topic"):
        print(f"by {field}: {repo.count(conn, by=field)}")


def _print_clause(c: Clause):
    print(f"{c.id}  (page {c.page}, {' > '.join(c.section_path)})")
    print(f"title: {c.title}\ntier: {c.tier}  status: {c.status}  topic: {c.topic}  notes: {c.notes}")
    print("-" * 60)
    print(c.text)


def cmd_show(conn, args):
    clause = repo.get_clause(conn, args.clause_id)
    if not clause:
        sys.exit(f"no clause {args.clause_id}")
    _print_clause(clause)


def cmd_search(conn, args):
    hits = repo.list_clauses(conn, search=args.text)
    for c in hits:
        print(f"{c.id:22} p{c.page:<4} {' '.join(c.text.split())[:100]}")
    print(f"{len(hits)} match(es)")


def cmd_mark(conn, args):
    clause = repo.get_clause(conn, args.clause_id)
    if not clause:
        sys.exit(f"no clause {args.clause_id}")
    updates = {f: getattr(args, f) for f in CURATED_FIELDS if getattr(args, f) is not None}
    if not updates:
        sys.exit("nothing to change: pass --tier, --topic, --status or --notes")
    clause = Clause(**{**clause.model_dump(), **updates})  # re-validates tier/status literals
    repo.upsert_clause(conn, clause)
    print(f"{clause.id}: " + ", ".join(f"{k}={v}" for k, v in updates.items()))


def cmd_export(conn, args):
    n = repo.export_selected(conn, args.yaml)
    print(f"exported {n} selected clause(s) to {args.yaml}")


def cmd_import(conn, args):
    n = repo.import_selected(conn, args.yaml)
    print(f"imported {n} clause(s) from {args.yaml}")


def cmd_suggest(conn, args):
    clauses = repo.list_clauses(conn)
    ranked = suggest(clauses, limit=args.limit)
    skipped = [c for c in clauses if len(c.text) > MAX_REVIEWABLE_CHARS]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(ranked, skipped), encoding="utf-8")
    print(f"wrote {len(ranked)} candidates to {args.out} (skipped {len(skipped)} oversized clauses)")


def cmd_review_export(conn, args):
    md = args.out.with_suffix(".md")
    n = review.export_sheet(args.units_yaml, args.pack, args.out, md)
    print(f"wrote {n} rule unit(s) to {args.out} and {md}")


def cmd_review_import(conn, args):
    try:
        result = review.import_sheet(args.sheet, args.units_yaml, args.pack, force=args.force)
    except review.ReviewImportError as e:
        print("review sheet rejected, nothing changed:")
        for err in e.errors:
            print(f"  {err}")
        sys.exit(1)
    print(f"changed: {', '.join(result.changed) or 'none'}; unchanged: {', '.join(result.unchanged) or 'none'}")
    print("note: the corpus DB is not updated; run `python -m app.corpus.cli unit-import` to load rule-units.yaml")


def cmd_unit_add(conn, args):
    unit = RuleUnit(id=f"{args.clause_id}#{args.suffix}", clause_id=args.clause_id, text=args.text,
                    tier=args.tier, notes=args.notes, expected_artifact=args.artifact)
    try:
        repo.upsert_unit(conn, unit)
    except ValueError as e:
        sys.exit(f"rejected: {e}")
    print(f"added {unit.id} (tier={unit.tier}, status={unit.status})")


def cmd_unit_list(conn, args):
    units = repo.list_units(conn, status=args.status)
    for u in units:
        print(f"{u.id:22} {u.tier:12} {u.status:8} reviewed={u.human_reviewed!s:5} {' '.join(u.text.split())[:70]}")
    print(f"{len(units)} unit(s)")


def cmd_unit_show(conn, args):
    u = repo.get_unit(conn, args.unit_id)
    if not u:
        sys.exit(f"no unit {args.unit_id}")
    for field, value in u.model_dump().items():
        print(f"{field}: {value}")


def cmd_unit_export(conn, args):
    print(f"exported {repo.export_units(conn, args.yaml)} unit(s) to {args.yaml}")


def cmd_unit_import(conn, args):
    print(f"imported {repo.import_units(conn, args.yaml)} unit(s) from {args.yaml}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m app.corpus.cli")
    parser.add_argument("--db", type=Path, default=repo.DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest")
    p.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    p.set_defaults(func=cmd_ingest)
    sub.add_parser("stats").set_defaults(func=cmd_stats)
    p = sub.add_parser("show")
    p.add_argument("clause_id")
    p.set_defaults(func=cmd_show)
    p = sub.add_parser("search")
    p.add_argument("text")
    p.set_defaults(func=cmd_search)
    p = sub.add_parser("mark")
    p.add_argument("clause_id")
    p.add_argument("--tier", choices=get_args(Tier))
    p.add_argument("--status", choices=get_args(Status))
    p.add_argument("--topic")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_mark)
    for name, func in (("export-selected", cmd_export), ("import-selected", cmd_import)):
        p = sub.add_parser(name)
        p.add_argument("--yaml", type=Path, default=DEFAULT_YAML)
        p.set_defaults(func=func)
    p = sub.add_parser("suggest")
    p.add_argument("--limit", type=int, default=80)
    p.add_argument("--out", type=Path, default=DEFAULT_CANDIDATES)
    p.set_defaults(func=cmd_suggest)

    p = sub.add_parser("unit-add")
    p.add_argument("clause_id")
    p.add_argument("--suffix", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--tier", choices=get_args(Tier), required=True)
    p.add_argument("--notes")
    p.add_argument("--artifact", help="path of the gold file, e.g. fixtures/ids/<unit>.ids")
    p.set_defaults(func=cmd_unit_add)
    from app.rulepack.loader import DEFAULT_PACK

    p = sub.add_parser("review-export", help="write the reviewer sheet (CSV with BOM for Excel, plus Markdown)")
    p.add_argument("--out", type=Path, default=REPO_ROOT / "docs" / "review" / "review-sheet.csv")
    p.add_argument("--units-yaml", type=Path, default=DEFAULT_UNITS_YAML)
    p.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    p.set_defaults(func=cmd_review_export)
    p = sub.add_parser("review-import", help="apply a filled review sheet (strict; --force to replace decisions)")
    p.add_argument("sheet", type=Path)
    p.add_argument("--units-yaml", type=Path, default=DEFAULT_UNITS_YAML)
    p.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_review_import)
    p = sub.add_parser("unit-list")
    p.add_argument("--status", choices=["pilot", "selected", "needs_rework", "rejected"])
    p.set_defaults(func=cmd_unit_list)
    p = sub.add_parser("unit-show")
    p.add_argument("unit_id")
    p.set_defaults(func=cmd_unit_show)
    for name, func in (("unit-export", cmd_unit_export), ("unit-import", cmd_unit_import)):
        p = sub.add_parser(name)
        p.add_argument("--yaml", type=Path, default=DEFAULT_UNITS_YAML)
        p.set_defaults(func=func)

    args = parser.parse_args(argv)
    conn = repo.connect(args.db)
    repo.init_db(conn)
    try:
        args.func(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
