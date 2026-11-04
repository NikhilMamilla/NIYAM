import json

import pytest

from app.audit.engine import audit
from app.fixtures.samples import GEO_SAMPLES, SAMPLES_DIR, build_samples
from app.rulepack.loader import load_rulepack

NAMES = list(GEO_SAMPLES)
GEO_RULES = ("MBBL2016-4.5.2#1", "MBBL2016-4.3.1.1#1", "MBBL2016-4.17.2#A")


def truth_of(name):
    return json.loads((SAMPLES_DIR / f"{name}.truth.json").read_text(encoding="utf-8"))


def truth_elements(truth):
    return [*truth["doors"], *truth["spaces"], *truth["stairs"]]


@pytest.fixture(scope="module")
def reports():
    pack = load_rulepack()
    return {name: audit(SAMPLES_DIR / f"{name}.ifc", pack) for name in NAMES}


@pytest.mark.parametrize("name", NAMES)
def test_committed_geometric_samples_regenerate_identically(name, tmp_path):
    build_samples(tmp_path)
    for suffix in (".ifc", ".truth.json"):
        committed = SAMPLES_DIR / f"{name}{suffix}"
        assert committed.exists(), f"missing {committed}; run scripts/build_sample_buildings.py"
        assert (tmp_path / committed.name).read_bytes().splitlines() == committed.read_bytes().splitlines()


@pytest.mark.parametrize("name", NAMES)
def test_audit_matches_truth_rule_by_rule_and_element_by_element(name, reports):
    truth, report = truth_of(name), reports[name]
    expected = {(rule, e["global_id"]): v for e in truth_elements(truth) for rule, v in e["expected"].items()}
    actual = {(r.unit_id, e.global_id): e.verdict for r in report.rules for e in r.elements
              if not (e.verdict == "out_of_scope" and (r.unit_id, e.global_id) not in expected)}
    mismatches = {k: (expected.get(k), actual.get(k)) for k in expected.keys() | actual.keys()
                  if expected.get(k) != actual.get(k)}
    assert not mismatches
    assert report.status == truth["expected_status"]
    assert all(r.status != "error" for r in report.rules)


@pytest.mark.parametrize("name", NAMES)
def test_summary_counts_equal_those_computed_from_the_truth_file(name, reports):
    truth, summary = truth_of(name), reports[name].summary
    elements = truth_elements(truth)
    checks = {"passed": 0, "failed": 0, "unchecked": 0, "out_of_scope": 0}
    for e in elements:
        for v in e["expected"].values():
            checks[v] += 1
    with_failed = sum("failed" in e["expected"].values() for e in elements)
    with_unchecked = sum("failed" not in e["expected"].values() and "unchecked" in e["expected"].values()
                         for e in elements)
    assert summary.checks.model_dump() == checks
    assert summary.elements.model_dump() == {
        "total_in_model_of_scoped_classes": len(elements), "with_failed": with_failed,
        "with_unchecked": with_unchecked, "clean": len(elements) - with_failed - with_unchecked}


@pytest.mark.parametrize("name", NAMES)
def test_every_geometric_rule_sees_passing_failing_unchecked_and_out_of_scope_elements(name):
    seen = {rule: set() for rule in GEO_RULES}
    for e in truth_elements(truth_of(name)):
        for rule, v in e["expected"].items():
            seen[rule].add(v)
    for rule, verdicts in seen.items():
        assert verdicts == {"passed", "failed", "unchecked", "out_of_scope"}, (rule, verdicts)


@pytest.mark.parametrize("name", NAMES)
def test_failed_and_unchecked_geometric_records_explain_themselves_with_numbers(name, reports):
    for r in reports[name].rules:
        if r.unit_id not in GEO_RULES:
            continue
        for e in r.elements:
            if e.verdict == "failed":
                assert e.reason_plain.startswith("Computed ") and "this rule requires at least" in e.reason_plain
                assert " m" in e.reason_plain and "measured" in e.reason_raw
            elif e.verdict == "unchecked":
                assert e.reason_plain and "could not be computed" in e.reason_plain \
                    or "does not declare" in e.reason_plain
            else:
                assert e.reason_plain is None


def test_sample_models_use_both_project_units():
    assert {truth_of(n)["length_unit"] for n in NAMES} == {"mm", "m"}
