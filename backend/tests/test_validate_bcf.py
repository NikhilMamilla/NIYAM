"""scripts/validate_bcf.py: an exported BCF passes the structure checks, a broken one does not."""

import importlib.util
import zipfile
from pathlib import Path

from app.audit.bcf_export import export_bcf
from app.audit.engine import audit
from app.rulepack.loader import DEFAULT_PACK, load_rulepack

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("validate_bcf", ROOT / "scripts" / "validate_bcf.py")
vb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vb)


def test_exported_bcf_is_structurally_valid_and_a_broken_one_is_not(tmp_path):
    good = tmp_path / "issues.bcf"
    export_bcf(audit(ROOT / "fixtures/samples/sample_a_mm.ifc", load_rulepack(DEFAULT_PACK)), good)
    problems, stats = vb.validate(good, None)
    assert problems == [] and stats["topics"] == stats["viewpoints"] > 0

    broken = tmp_path / "broken.bcf"
    with zipfile.ZipFile(good) as src, zipfile.ZipFile(broken, "w") as dst:
        for n in src.namelist():
            if n != "bcf.version" and not n.endswith(".bcfv"):
                dst.writestr(n, src.read(n))
    problems, _ = vb.validate(broken, None)
    assert any("bcf.version" in p for p in problems) and any("viewpoint" in p for p in problems)
