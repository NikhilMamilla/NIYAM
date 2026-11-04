import json

import pytest

from app.audit.engine import audit
from app.fixtures.samples import SAMPLES, SAMPLES_DIR, build_samples
from app.rulepack.loader import load_rulepack


@pytest.mark.parametrize("name", SAMPLES)
def test_committed_samples_regenerate_identically(name, tmp_path):
    build_samples(tmp_path)
    for suffix in (".ifc", ".truth.json"):
        committed = SAMPLES_DIR / f"{name}{suffix}"
        assert committed.exists(), f"missing {committed}; run scripts/build_sample_buildings.py"
        assert (tmp_path / committed.name).read_bytes().splitlines() == committed.read_bytes().splitlines()


@pytest.mark.parametrize("name", SAMPLES)
def test_audit_matches_truth_element_by_element(name):
    truth = json.loads((SAMPLES_DIR / f"{name}.truth.json").read_text(encoding="utf-8"))
    report = audit(SAMPLES_DIR / f"{name}.ifc", load_rulepack())

    expected = {(rule, d["global_id"]): v for d in truth["doors"] for rule, v in d["expected"].items()}
    actual = {(r.unit_id, e.global_id): e.verdict for r in report.rules for e in r.elements}
    mismatches = {k: (expected.get(k), actual.get(k)) for k in expected.keys() | actual.keys()
                  if expected.get(k) != actual.get(k)}
    assert not mismatches
    assert report.status == truth["expected_status"]


@pytest.mark.parametrize("name", SAMPLES)
def test_samples_cover_every_required_case(name):
    truth = json.loads((SAMPLES_DIR / f"{name}.truth.json").read_text(encoding="utf-8"))
    assert truth["synthetic"] is True and 10 <= len(truth["doors"]) <= 12
    assert {d["storey"] for d in truth["doors"]} == {"Ground floor", "First floor"}
    ops = {d["operation_type"] for d in truth["doors"] if d["fire_exit"] is True}
    assert {"REVOLVING", "ROLLINGUP"} <= ops and any(o.startswith("SLIDING") for o in ops)
    assert sum(d["fire_exit"] is None for d in truth["doors"]) >= 2
    assert any(d["fire_exit"] is False for d in truth["doors"])
    assert any(d["expected"]["MBBL2016-5.4.1#b"] == "failed" for d in truth["doors"])
    if name == "sample_a_mm":
        [no_width] = [d for d in truth["doors"] if d["fire_exit"] is True and d["width_m"] is None]
        assert no_width["expected"] == {"MBBL2016-5.4.2#1": "passed", "MBBL2016-5.4.1#b": "unchecked",
                                        "MBBL2016-5.4.1#c": "passed"}
