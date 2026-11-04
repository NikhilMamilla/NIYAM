"""Regenerate the synthetic sample buildings fixtures/samples/*.ifc and their *.truth.json,
plus fixtures/invalid/ifc2x3_minimal.ifc (used to test that non-IFC4 uploads are refused).

Run from backend/ with the venv active:  python ../scripts/build_sample_buildings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.fixtures.samples import build_ifc2x3, build_samples  # noqa: E402

for path in build_samples():
    print(f"wrote {path.name} and {path.stem}.truth.json")
print(f"wrote {build_ifc2x3().name}")
