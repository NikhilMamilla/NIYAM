import hashlib

import pytest

from app.eval.scoring import score_candidate
from app.fixtures.builders import REPO_ROOT
from app.fixtures.gold_ids import load_units
from app.specgen import generator
from app.specgen.models import load_all
from app.verifier.geometric_gate import validate_source

SPECS = {s.unit_id: s for s in load_all()}
ONE_PER_TEMPLATE = {s.template: s for s in reversed(list(SPECS.values()))}
CHECKSUMS = REPO_ROOT / "backend" / "tests" / "data" / "phase8_fixture_checksums.txt"


def test_existing_fixtures_are_byte_identical_to_phase8():
    lines = CHECKSUMS.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 53
    for line in lines:
        digest, name = line.split(" ", 1)
        path = REPO_ROOT / name.lstrip("*")
        # checksums were taken from LF files; a Windows checkout with core.autocrlf rewrites them to CRLF
        assert hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest, path


def test_specs_cover_all_four_templates_and_are_registered_as_draft_pilots():
    assert set(ONE_PER_TEMPLATE) == {"door_width_min", "door_operation_forbidden", "space_area_min",
                                     "space_height_min"}
    units = load_units()
    for unit_id, spec in SPECS.items():
        u = units[unit_id]
        assert (u.tier, u.status, u.human_reviewed, u.text) == (spec.tier, "pilot", False, spec.unit_text)


@pytest.mark.parametrize("unit_id", sorted(SPECS))
def test_build_is_deterministic(unit_id, tmp_path):
    spec = SPECS[unit_id]
    dirs = {k: tmp_path / k for k in ("ifc", "held", "gold", "dry")}
    for d in dirs.values():
        d.mkdir()
    built = generator.build_files(spec, fixtures_dir=dirs["ifc"], heldout_dir=dirs["held"],
                                  artifact_dir=dirs["gold"], dryrun_dir=dirs["dry"])
    committed = {"dev_pass": generator.dev_pair(spec).pass_path, "dev_fail": generator.dev_pair(spec).fail_path,
                 **{f"heldout_{k}": v for k, v in generator.heldout_paths(spec).items() if k != "truth"},
                 "truth": generator.heldout_paths(spec)["truth"], "gold": generator.gold_artifact(spec)[0]}
    for key, path in committed.items():
        assert built[key].read_bytes().splitlines() == path.read_bytes().splitlines(), key
    for answer in (dirs["dry"] / spec.safe).iterdir():
        assert answer.read_bytes() == (generator.DRYRUN_DIR / spec.safe / answer.name).read_bytes()


@pytest.mark.parametrize("unit_id", sorted(SPECS))
def test_generated_gold_passes_the_gate_and_the_heldout_truth(unit_id):
    spec = SPECS[unit_id]
    path, text = generator.gold_artifact(spec)
    assert path.read_text(encoding="utf-8") == text
    if spec.tier == "geometric":
        validate_source(text)  # only existing helpers, inside the AST allowlist
    score = score_candidate(load_units()[unit_id], text)
    assert score.error is None and score.heldout_mismatches == []
    assert (score.valid, score.dev_correct, score.heldout_correct, score.vacuous) == (True, True, True, False)


@pytest.mark.parametrize("unit_id", sorted(SPECS))
def test_heldout_truth_is_arithmetic_and_has_a_boundary_pair(unit_id):
    spec = SPECS[unit_id]
    elements = [e for kind in generator.heldout_elements(spec).values() for e in kind]
    assert {e.name for e in elements}.isdisjoint({e.name for k in generator.dev_elements(spec).values() for e in k})
    if spec.threshold is None:
        assert {generator.expected(spec, e) for e in elements} == {"pass", "fail", "out_of_scope"}
        return
    t = spec.threshold.value
    at_bound = [e for e in elements if e.value == t and e.selected]
    assert at_bound and generator.expected(spec, at_bound[0]) == ("pass" if spec.threshold.inclusive else "fail")
    assert any(e.selected and generator.expected(spec, e) == "fail" and abs(e.value - t) <= 0.0101 for e in elements)


@pytest.mark.parametrize("template", sorted(ONE_PER_TEMPLATE))
def test_overfit_mutation_passes_dev_but_fails_heldout(template):
    spec = ONE_PER_TEMPLATE[template]
    if template == "door_operation_forbidden" and len(spec.params.forbidden_operations) == 1:
        spec = SPECS["MBBL2016-4.24.7.2#c"]
    score = score_candidate(load_units()[spec.unit_id], generator.overfit(spec))
    assert score.valid and score.dev_correct and not score.heldout_correct, score
    assert all(m["expected"] == "fail" and m["got"] == "pass" for m in score.heldout_mismatches)


def test_inclusive_vs_exclusive_is_caught_by_the_dev_boundary():
    spec = ONE_PER_TEMPLATE["space_height_min"]
    strict = generator.gold_check(spec, inclusive=False)  # ">" where the clause says "not less than"
    score = score_candidate(load_units()[spec.unit_id], strict)
    assert score.valid and not score.dev_correct and not score.heldout_correct
