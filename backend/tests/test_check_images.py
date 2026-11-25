"""scripts/check_images.py: every published image is referenced and exists, with one caption each."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_images_are_referenced_exist_and_say_one_thing():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_images.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
