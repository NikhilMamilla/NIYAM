"""python -m app.specgen.cli validate <spec>|--all | build <spec>|--all | status"""

import argparse
import sys
from pathlib import Path

from app.fixtures.heldout import HELDOUT_DIR
from app.specgen import generator
from app.specgen.models import SpecError, load_all, load_spec, spec_paths


def _specs(args):
    return load_all() if args.all else [load_spec(Path(args.spec))]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.specgen.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build"):
        p = sub.add_parser(name)
        p.add_argument("spec", nargs="?")
        p.add_argument("--all", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    if args.command in ("validate", "build") and not (args.all or args.spec):
        parser.error("give a spec file or --all")
    try:
        if args.command == "validate":
            for spec in _specs(args):
                print(f"OK  {spec.unit_id:22} {spec.template:26} {spec.tier}")
        elif args.command == "build":
            specs = _specs(args)
            for spec in specs:
                files = generator.build_files(spec)
                print(f"built {spec.unit_id}: {', '.join(p.name for p in files.values())}")
            generator.register_units(load_all())  # always the full set, so rule-units.yaml stays complete
            print(f"registered {len(specs)} unit(s) in rules/corpus/rule-units.yaml (and the corpus DB if present)")
        else:
            for path in spec_paths():
                try:
                    spec = load_spec(path)
                except SpecError as e:
                    print(f"INVALID {path.name}: {e}")
                    continue
                built = all(p.exists() for p in generator.heldout_paths(spec, HELDOUT_DIR).values()) and \
                    generator.gold_artifact(spec)[0].exists()
                print(f"{spec.unit_id:22} {spec.template:26} {'built' if built else 'NOT BUILT'}")
    except SpecError as e:
        print(f"INVALID: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
