import ifcopenshell
import pytest

from app.fixtures.builders import FIXTURES_DIR, PILOT_UNITS, build_all, fixture_pair, safe_name


def test_safe_name_is_filesystem_safe():
    assert safe_name("MBBL2016-5.4.1#b") == "MBBL2016-5_4_1_b"


@pytest.mark.parametrize("unit_id", PILOT_UNITS)
def test_committed_fixtures_exist_and_regenerate_identically(unit_id, tmp_path):
    build_all(tmp_path)
    for kind in ("pass", "fail"):
        committed = FIXTURES_DIR / f"{safe_name(unit_id)}__{kind}.ifc"
        assert committed.exists(), f"missing {committed}; run scripts/build_fixtures.py"
        regenerated = tmp_path / committed.name
        # line endings may be rewritten by git checkout on another OS; content must not change
        assert regenerated.read_bytes().splitlines() == committed.read_bytes().splitlines()


@pytest.mark.parametrize(
    "unit_id, changed_lines",
    [("MBBL2016-5.4.2#1", 1), ("MBBL2016-5.4.1#b", 2), ("MBBL2016-5.4.1#c", 1)],
)
def test_pair_differs_only_in_the_rule_value(unit_id, changed_lines):
    pair = fixture_pair(unit_id)
    pass_lines = pair.pass_path.read_text().splitlines()
    fail_lines = pair.fail_path.read_text().splitlines()
    assert len(pass_lines) == len(fail_lines)
    diff = [(a, b) for a, b in zip(pass_lines, fail_lines) if a != b]
    assert len(diff) == changed_lines, diff


@pytest.mark.parametrize("unit_id", PILOT_UNITS)
def test_global_ids_are_unique_within_each_fixture(unit_id):
    pair = fixture_pair(unit_id)
    for path in (pair.pass_path, pair.fail_path):
        ids = [e.GlobalId for e in ifcopenshell.open(str(path)).by_type("IfcRoot")]
        assert len(ids) == len(set(ids)), path.name


@pytest.mark.parametrize("unit_id", PILOT_UNITS)
def test_expected_failing_entity_is_a_fire_exit_door_in_both_fixtures(unit_id):
    pair = fixture_pair(unit_id)
    for path in (pair.pass_path, pair.fail_path):
        model = ifcopenshell.open(str(path))
        doors = {d.GlobalId: d for d in model.by_type("IfcDoor")}
        assert pair.expected_failing <= doors.keys()
        assert len(doors) >= 2  # door under test plus a non-exit control door
