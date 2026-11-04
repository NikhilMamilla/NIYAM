import argparse
import sys
from pathlib import Path

from app.corpus import repository as repo
from app.fixtures.builders import fixture_pair, safe_name
from app.rulepack.loader import DEFAULT_PACK, RulepackError, load_rulepack, read_manifest, scope_from_ids, write_manifest
from app.rulepack.models import Manifest, Rule
from app.verifier.ids_gate import verify_ids


def cmd_add(args) -> int:
    if not args.gate:
        sys.exit("refusing to add without --gate: only gate-accepted IDS enter the rulepack")
    conn = repo.connect(args.db)
    repo.init_db(conn)
    unit = repo.get_unit(conn, args.unit_id)
    clause = repo.get_clause(conn, unit.clause_id) if unit else None
    conn.close()
    if clause is None:
        sys.exit(f"unit {args.unit_id} or its clause is not in the corpus DB {args.db}")
    try:
        fixtures = fixture_pair(unit.id)
    except KeyError:
        sys.exit(f"no fixtures for {unit.id}: the gate needs a pass/fail fixture pair")

    xml = args.ids_file.read_text(encoding="utf-8")
    result = verify_ids(xml, unit, fixtures)
    for s in result.stage_results:
        print(f"{s.stage:24} {'PASS' if s.passed else 'FAIL':5} {s.message}")
    if not result.accepted:
        print(f"REJECTED at {result.first_failure.stage}; rulepack unchanged")
        return 1

    ids_file = f"ids/{safe_name(unit.id)}.ids"
    (args.pack / "ids").mkdir(parents=True, exist_ok=True)
    (args.pack / ids_file).write_text(xml, encoding="utf-8")
    rule = Rule(unit_id=unit.id, clause_id=clause.id, clause_text=clause.text, rule_text=unit.text,
                ids_file=ids_file, scope=scope_from_ids(xml), source_doc=clause.source_doc, page=clause.page,
                human_reviewed=unit.human_reviewed)
    manifest = read_manifest(args.pack) or Manifest(version=args.pack.name, rules=[])
    manifest.rules = [r for r in manifest.rules if r.unit_id != unit.id] + [rule]
    write_manifest(args.pack, manifest)
    load_rulepack(args.pack)  # the pack must still validate after the change
    print(f"ACCEPTED: added {unit.id} to {args.pack}")
    return 0


def cmd_list(args) -> int:
    pack = load_rulepack(args.pack)
    print(f"rulepack {pack.manifest.version} ({pack.root})")
    for r in pack.manifest.rules:
        data = ", ".join(d.key for d in r.scope.required_data)
        print(f"{r.unit_id:18} {r.clause_id:16} p{r.page:<4} {r.severity:6} reviewed={r.human_reviewed!s:5} "
              f"{r.scope.ifc_class} [{data}]  {r.rule_text}")
    return 0


def cmd_validate(args) -> int:
    try:
        pack = load_rulepack(args.pack)
    except RulepackError as e:
        print(f"INVALID: {e}")
        return 1
    print(f"{len(pack.manifest.rules)} rule(s) valid in {pack.root}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.rulepack.cli")
    parser.add_argument("--db", type=Path, default=repo.DEFAULT_DB)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add", help="gate an IDS against the unit's fixtures and add it only if accepted")
    p.add_argument("unit_id")
    p.add_argument("ids_file", type=Path)
    p.add_argument("--gate", action="store_true", help="required: run the full verifier gate")
    p.set_defaults(func=cmd_add)
    sub.add_parser("list").set_defaults(func=cmd_list)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
