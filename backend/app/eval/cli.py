"""python -m app.eval.cli plan | preflight | run --yes [--dry-run] | report <results.json> | slides <results.json>"""

import argparse
import sys
from pathlib import Path

from app.eval import preflight, report, runner, slides
from app.eval.dryrun import DryRunProvider
from app.fixtures.builders import REPO_ROOT
from app.llm.base import ProviderNotConfigured
from app.llm.factory import get_provider

DEFAULT_CONFIG = REPO_ROOT / "eval" / "config.yaml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.eval.cli")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("preflight", help="one tiny live call per configured model; never compiles")
    p = sub.add_parser("run")
    p.add_argument("--yes", action="store_true", help="required: confirm the planned LLM calls")
    p.add_argument("--dry-run", action="store_true", help="synthetic DryRunProvider answers; never model results")
    p.add_argument("--runs-dir", type=Path, default=runner.RUNS_DIR)
    p.add_argument("--no-report", action="store_true")
    p.add_argument("--skip-preflight", action="store_true", help="run without a recent successful preflight")
    p = sub.add_parser("report")
    p.add_argument("results", type=Path)
    p.add_argument("--out", type=Path)
    p = sub.add_parser("slides", help="slide data (md + csv) for a real, committed run; refuses dry runs")
    p.add_argument("results", type=Path)
    p.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.command in ("report", "slides"):
        write = report.write_report if args.command == "report" else slides.write_slides
        try:
            for path in write(args.results, args.out):
                print(f"wrote {path}")
        except report.RefusedOutput as e:
            print(f"REFUSED: {e}")
            return 2
        return 0

    if not args.config.exists():
        sys.exit(f"no config at {args.config}: copy eval/config.example.yaml to eval/config.yaml")
    config = runner.load_config(args.config)
    if args.command == "preflight":
        return preflight.run_preflight(config)
    plan = runner.make_plan(config)
    for line in plan.lines(config):
        print(line)
    if not plan.within_budget:
        return 2
    if args.command == "plan":
        for line in plan.estimate_lines(config):
            print(line)
        return 0
    if not args.yes:
        print("not running: pass --yes to confirm the LLM calls above")
        return 2
    if args.dry_run:
        factory = lambda name, mode: DryRunProvider(seed=name)  # noqa: E731 - fresh per model and mode
        providers = None
    else:
        if args.skip_preflight:
            print("WARNING: skipping the preflight: provider problems will only show up after calls are spent")
        else:
            ok, reason = preflight.check_stamp(config)
            print(reason)
            if not ok:
                return 2
        factory, providers = None, {}
        for spec in config.models:
            try:
                providers[spec.name] = get_provider(spec.role)
            except ProviderNotConfigured as e:
                print(f"model {spec.name} ({spec.role}) is not configured: {e}")
                return 2
    run_dir = runner.run(config, providers, dry_run=args.dry_run, runs_dir=args.runs_dir, provider_factory=factory)
    print(f"results: {run_dir / 'results.json'}")
    if not args.no_report:
        for path in report.write_report(run_dir / "results.json"):
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
