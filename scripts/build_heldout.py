"""Regenerate fixtures/heldout/: held-out pairs and hand-written truth for the evaluation harness.

Run from backend/ with the venv active:  python ../scripts/build_heldout.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.fixtures.heldout import build_all  # noqa: E402

for p in build_all():
    print(f"wrote {p['pass'].name}, {p['fail'].name}, {p['truth'].name}")
