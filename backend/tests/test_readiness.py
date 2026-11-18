import re

import ifcopenshell
from ifctester import ids

from app.fixtures.builders import REPO_ROOT
from app.rulepack import cli, readiness
from app.specgen.models import load_all
from app.verifier.ids_gate import static_check

SAMPLE_A = REPO_ROOT / "fixtures" / "samples" / "sample_a_mm.ifc"
REAL = REPO_ROOT / "fixtures" / "real" / "buildingsmart" / "Building-Architecture.ifc"


def run(xml: str, path) -> dict[str, tuple[bool, int]]:
    """{specification name: (passed, number of failing entities)} from a real ifctester run."""
    doc = ids.from_string(xml)
    doc.validate(ifcopenshell.open(str(path)))
    return {s.name: (bool(s.status), len(s.failed_entities)) for s in doc.specifications}


def test_readiness_ids_passes_the_static_ids_gate_and_loads_in_ifctester():
    xml = readiness.build_ids()
    assert static_check(xml).accepted, static_check(xml).first_failure
    assert len(ids.from_string(xml).specifications) == 6


def test_categories_come_from_the_rules_not_from_a_list():
    xml = readiness.build_ids()
    spec_categories = {c for s in load_all() for c in (s.params.categories or [])}
    expected = spec_categories | {"Habitable", "Bathroom"}  # the two hand-written v0 room checks
    assert set(re.findall(r'<xs:enumeration value="([^"]+)"', xml)) == expected
    assert "Corridor" not in expected  # in the profile, but no rule uses it


def test_every_requirement_names_the_units_it_enables():
    for spec in ids.from_string(readiness.build_ids()).specifications:
        assert re.search(r"(MBBL2016|TGBR2012)-[\d.]+#", spec.instructions), spec.name
    by_name = {s.name: s.instructions for s in ids.from_string(readiness.build_ids()).specifications}
    assert "TGBR2012-5#c" in by_name["Spaces declare a profile Category"]
    assert "MBBL2016-5.4.1#b2" in by_name["Exit doors carry Qto_DoorBaseQuantities.Height"]
    assert "MBBL2016-4.17.2#A" in by_name["Buildings declare Pset_BuildingCommon.OccupancyType"]


def test_on_sample_a_some_requirements_pass_and_some_fail():
    results = run(readiness.build_ids(), SAMPLE_A)
    assert any(ok for ok, _ in results.values()) and not all(ok for ok, _ in results.values())


def test_on_the_real_model_spaces_fail_for_the_missing_category():
    results = run(readiness.build_ids(), REAL)
    assert results["Spaces declare a profile Category"] == (False, 2)


def test_cli_writes_the_committed_file_and_it_is_current(tmp_path):
    out = tmp_path / "r.ids"
    assert cli.main(["readiness", "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == readiness.build_ids()
    assert readiness.DEFAULT_OUT.read_text(encoding="utf-8") == readiness.build_ids()
