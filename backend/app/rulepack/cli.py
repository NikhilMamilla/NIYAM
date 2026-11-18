import argparse
import sys
from pathlib import Path

from app.corpus import repository as repo
from app.fixtures.builders import fixture_pair, safe_name
from app.rulepack.loader import (DEFAULT_PACK, RulepackError, load_rulepack, read_manifest, scope_from_check,
                                 scope_from_ids, write_manifest)
from app.rulepack.models import Manifest, Rule
from app.verifier.geometric_gate import verify_geometric
from app.verifier.ids_gate import verify_ids


def cmd_add(args) -> int:
    if not args.gate:
        sys.exit("refusing to add without --gate: only gate-accepted rules enter the rulepack")
    conn = repo.connect(args.db)
    repo.init_db(conn)
    unit = repo.get_unit(conn, args.unit_id)
    clause = repo.get_clause(conn, unit.clause_id) if unit else None
    conn.close()
    if clause is None:
        sys.exit(f"unit {args.unit_id} or its clause is not in the corpus DB {args.db}")
    if unit.tier not in ("ids", "geometric"):
        sys.exit(f"unit {unit.id} has tier {unit.tier}: only ids and geometric rules can be added")
    try:
        fixtures = fixture_pair(unit.id)
    except KeyError:
        sys.exit(f"no fixtures for {unit.id}: the gate needs a pass/fail fixture pair")

    source = args.ids_file.read_text(encoding="utf-8")
    geometric = unit.tier == "geometric"
    if geometric:
        result = verify_geometric(source, unit, fixtures, timeout_s=args.timeout)
    else:
        result = verify_ids(source, unit, fixtures)
    for s in result.stage_results:
        print(f"{s.stage:32} {'PASS' if s.passed else 'FAIL':5} {s.message}")
    if not result.accepted:
        print(f"REJECTED at {result.first_failure.stage}; rulepack unchanged")
        return 1

    folder, suffix = ("checks", ".py") if geometric else ("ids", ".ids")
    artifact = f"{folder}/{safe_name(unit.id)}{suffix}"
    (args.pack / folder).mkdir(parents=True, exist_ok=True)
    (args.pack / artifact).write_text(source, encoding="utf-8")
    common = dict(unit_id=unit.id, clause_id=clause.id, clause_text=clause.text, rule_text=unit.text,
                  source_doc=clause.source_doc, page=clause.page, human_reviewed=unit.human_reviewed)
    if geometric:
        rule = Rule(**common, tier=unit.tier, scope=scope_from_check(source), check_file=artifact)
    else:
        rule = Rule(**common, ids_file=artifact, scope=scope_from_ids(source))
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
        print(f"{r.unit_id:18} {r.tier:9} {r.clause_id:16} p{r.page:<4} {r.severity:6} reviewed={r.human_reviewed!s:5} "
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


def cmd_readiness(args) -> int:
    from app.rulepack import readiness

    out = args.out or readiness.DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(readiness.build_ids(), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.rulepack.cli")
    parser.add_argument("--db", type=Path, default=repo.DEFAULT_DB)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add", help="gate an IDS against the unit's fixtures and add it only if accepted")
    p.add_argument("unit_id")
    p.add_argument("ids_file", type=Path, help="the IDS file (ids tier) or Python check (geometric tier)")
    p.add_argument("--gate", action="store_true", help="required: run the verifier gate for the unit's tier")
    p.add_argument("--timeout", type=float, default=60.0, help="sandbox timeout for geometric checks, seconds")
    p.set_defaults(func=cmd_add)
    sub.add_parser("list").set_defaults(func=cmd_list)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    p = sub.add_parser("readiness", help="write one IDS listing the data a model needs for the rules to be checkable")
    p.add_argument("--out", type=Path, default=None)
    p.set_defaults(func=cmd_readiness)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
