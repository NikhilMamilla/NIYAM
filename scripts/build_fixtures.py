"""Regenerate fixtures/ifc/<unit>__pass.ifc and __fail.ifc for every pilot rule unit.

Run from backend/ with the venv active:  python ../scripts/build_fixtures.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.fixtures.builders import build_all  # noqa: E402

for pair in build_all():
    print(f"wrote {pair.pass_path.name}, {pair.fail_path.name}")
