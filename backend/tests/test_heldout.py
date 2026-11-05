import pytest

from app.eval.scoring import score_candidate
from app.fixtures import heldout
from app.fixtures.builders import REPO_ROOT, fixture_pair, safe_name
from app.fixtures.gold_ids import GOLD_DIR, load_units

CHECKS = REPO_ROOT / "fixtures" / "checks"
QUANTITATIVE = ["MBBL2016-5.4.1#b", "MBBL2016-4.5.2#1", "MBBL2016-4.3.1.1#1", "MBBL2016-4.17.2#A"]


def gold(unit_id):
    unit = load_units()[unit_id]
    path = GOLD_DIR / f"{safe_name(unit_id)}.ids" if unit.tier == "ids" else CHECKS / f"{safe_name(unit_id)}.py"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("unit_id", heldout.UNITS)
def test_heldout_regenerates_identically(unit_id, tmp_path):
    built, committed = heldout.build(unit_id, tmp_path), heldout.paths(unit_id)
    for key in ("pass", "fail", "truth"):
        assert committed[key].exists(), f"missing {committed[key]}; run scripts/build_heldout.py"
        assert built[key].read_bytes().splitlines() == committed[key].read_bytes().splitlines()


@pytest.mark.parametrize("unit_id", heldout.UNITS)
def test_gold_artifact_gives_exactly_the_heldout_truth(unit_id):
    score = score_candidate(load_units()[unit_id], gold(unit_id))
    assert score.error is None and score.heldout_mismatches == []
    assert (score.valid, score.dev_correct, score.heldout_correct, score.vacuous) == (True, True, True, False)


@pytest.mark.parametrize("unit_id", QUANTITATIVE)
def test_every_quantitative_unit_has_a_boundary_pair(unit_id):
    elements = [e for model in heldout.load_truth(unit_id)["models"].values() for e in model]
    assert any("exactly" in e["name"] and e["expected"] == "pass" for e in elements)
    assert any(e["expected"] == "fail" and ("0.99" in e["name"] or "1.79" in e["name"] or "2.74" in e["name"])
               for e in elements)


@pytest.mark.parametrize("unit_id", heldout.UNITS)
def test_heldout_differs_from_the_dev_pair(unit_id):
    import ifcopenshell

    dev = fixture_pair(unit_id)
    dev_names = {e.Name for p in (dev.pass_path, dev.fail_path) for e in ifcopenshell.open(str(p)).by_type("IfcRoot")}
    dev_ids = {e.GlobalId for p in (dev.pass_path, dev.fail_path) for e in ifcopenshell.open(str(p)).by_type("IfcRoot")}
    for model in heldout.load_truth(unit_id)["models"].values():
        for e in model:
            assert e["name"] not in dev_names and e["global_id"] not in dev_ids
    assert heldout.load_truth(unit_id)["length_unit"] == "m"  # dev pairs are millimetre projects


def test_overfit_ids_rule_passes_the_dev_gate_but_fails_heldout():
    # tuned to the dev pair (1.0 m passes, 0.9 m fails) instead of the clause: 0.95 m
    overfit = gold("MBBL2016-5.4.1#b").replace('value="1.0"', 'value="0.95"')
    assert overfit != gold("MBBL2016-5.4.1#b")
    score = score_candidate(load_units()["MBBL2016-5.4.1#b"], overfit)
    assert score.valid and score.dev_correct and not score.heldout_correct
    assert score.heldout_mismatches == [{"model": "MBBL2016-5_4_1_b__heldout_fail.ifc", "element": "HO exit 0.99 m",
                                         "expected": "fail", "got": "pass"}]


def test_overfit_geometric_rule_passes_the_dev_gate_but_fails_heldout():
    # threshold between the dev pass (1.8 m2) and fail (1.68 m2) values instead of the clause's 1.8 m2
    overfit = gold("MBBL2016-4.5.2#1").replace("required = 1.8", "required = 1.7")
    assert overfit != gold("MBBL2016-4.5.2#1")
    score = score_candidate(load_units()["MBBL2016-4.5.2#1"], overfit)
    assert score.valid and score.dev_correct and not score.heldout_correct
    assert [m["element"] for m in score.heldout_mismatches] == ["HO bath 1.79 m2"]


def test_strict_inequality_is_caught_by_the_heldout_boundary():
    # ">" instead of ">=": exactly 1.0 m must pass
    strict = gold("MBBL2016-4.17.2#A").replace("width < required - 1e-9", "width <= required")
    score = score_candidate(load_units()["MBBL2016-4.17.2#A"], strict)
    assert not score.heldout_correct
    assert "HO flight exactly 1.0 m" in [m["element"] for m in score.heldout_mismatches]


def test_scoring_never_raises():
    unit = load_units()["MBBL2016-4.5.2#1"]
    assert score_candidate(unit, None).error == "no candidate"
    broken = score_candidate(unit, "def check(model, helpers):\n    return 1 / 0\n")
    assert not broken.valid and broken.error is None
    assert not score_candidate(load_units()["MBBL2016-5.4.2#1"], "<ids").valid
