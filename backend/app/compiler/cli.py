import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.compiler.ids_compiler import compile_unit
from app.corpus import repository as repo
from app.fixtures.builders import PILOT_UNITS, REPO_ROOT
from app.fixtures.gold_ids import load_units
from app.llm.base import ProviderNotConfigured
from app.llm.factory import get_provider

DEFAULT_RUNS_DIR = REPO_ROOT / "eval" / "runs"


def _compile(unit_ids, args) -> int:
    try:
        provider = get_provider(args.role)
    except ProviderNotConfigured as e:
        sys.exit(str(e))
    units = load_units()
    conn = repo.connect(args.db)
    repo.init_db(conn)
    run_dir = args.runs_dir / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"{'unit':20} {'outcome':18} {'repairs':>7} {'tokens':>7} {'secs':>6}")
    accepted = True
    for unit_id in unit_ids:
        clause = repo.get_clause(conn, units[unit_id].clause_id) if unit_id in units else None
        if clause is None:
            sys.exit(f"unknown unit {unit_id} or its clause is not in the corpus DB (run the corpus ingest first)")
        r = compile_unit(units[unit_id], clause, provider, use_gate=not args.no_gate,
                         max_repairs=args.max_repairs, run_dir=run_dir)
        accepted &= r.outcome in ("accepted", "baseline_scored")
        print(f"{unit_id:20} {r.outcome:18} {r.repair_rounds:>7} {r.total_tokens:>7} {r.wall_time_s:>6.1f}")
    conn.close()
    print(f"results: {run_dir}")
    return 0 if accepted else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.compiler.cli")
    parser.add_argument("--db", type=Path, default=repo.DEFAULT_DB)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("compile", "compile-all-pilots"):
        p = sub.add_parser(name)
        if name == "compile":
            p.add_argument("unit_id")
        p.add_argument("--role", choices=["hosted", "open"], required=True)
        p.add_argument("--no-gate", action="store_true", help="ablation baseline: one call, gate only scores")
        p.add_argument("--max-repairs", type=int, default=3)
    args = parser.parse_args(argv)
    return _compile([args.unit_id] if args.command == "compile" else PILOT_UNITS, args)


if __name__ == "__main__":
    sys.exit(main())
