import argparse
import sys
from pathlib import Path

from app.fixtures.builders import fixture_pair
from app.fixtures.gold_ids import load_units
from app.verifier import geometric_gate
from app.verifier.ids_gate import STAGES, verify_ids


def cmd_check(args) -> int:
    units = load_units()
    if args.unit_id not in units:
        sys.exit(f"no unit {args.unit_id} in rules/corpus/rule-units.yaml")
    result = verify_ids(args.ids_file.read_text(encoding="utf-8"), units[args.unit_id], fixture_pair(args.unit_id))
    ran = {s.stage: s for s in result.stage_results}
    print(f"{args.unit_id}  <-  {args.ids_file.name}")
    print(f"{'stage':24} {'result':8} message")
    for name in STAGES:
        s = ran.get(name)
        status = "-" if s is None else ("PASS" if s.passed else "FAIL")
        print(f"{name:24} {status:8} {'(not run)' if s is None else s.message}")
    print("ACCEPTED" if result.accepted else f"REJECTED at {result.first_failure.stage}")
    return 0 if result.accepted else 1


def cmd_check_geo(args) -> int:
    units = load_units()
    if args.unit_id not in units:
        sys.exit(f"no unit {args.unit_id} in rules/corpus/rule-units.yaml")
    result = geometric_gate.verify_geometric(args.py_file.read_text(encoding="utf-8"), units[args.unit_id],
                                             fixture_pair(args.unit_id), timeout_s=args.timeout)
    ran = {s.stage: s for s in result.stage_results}
    print(f"{args.unit_id}  <-  {args.py_file.name}")
    print(f"{'stage':32} {'result':8} message")
    for name in geometric_gate.STAGES:
        s = ran.get(name)
        status = "-" if s is None else ("PASS" if s.passed else "FAIL")
        print(f"{name:32} {status:8} {'(not run)' if s is None else s.message}")
    print("ACCEPTED" if result.accepted else f"REJECTED at {result.first_failure.stage}")
    return 0 if result.accepted else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.verifier.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("unit_id")
    p.add_argument("ids_file", type=Path)
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("check-geo", help="run a generated geometric check through the sandboxed gate")
    p.add_argument("unit_id")
    p.add_argument("py_file", type=Path)
    p.add_argument("--timeout", type=float, default=geometric_gate.sandbox.DEFAULT_TIMEOUT_S)
    p.set_defaults(func=cmd_check_geo)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
