"""Regenerate draft gold IDS files fixtures/ids/<unit>.ids from rules/corpus/rule-units.yaml.

Run from backend/ with the venv active:  python ../scripts/build_gold_ids.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.fixtures.gold_ids import build_all_gold  # noqa: E402

for path in build_all_gold():
    print(f"wrote {path.name}")
