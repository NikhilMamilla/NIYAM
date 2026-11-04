import ifcopenshell
import pytest

from app.fixtures import geo_builders as gb
from app.fixtures.builders import guid, new_model, run
from app.geometry import helpers as h

AREA, HEIGHT, STAIR = "MBBL2016-4.5.2#1", "MBBL2016-4.3.1.1#1", "MBBL2016-4.17.2#A"


@pytest.fixture(scope="module")
def models(tmp_path_factory):
    out = tmp_path_factory.mktemp("geo")
    loaded = {}
    for unit_id in gb.UNITS:
        for unit in ("mm", "m"):
            pair = gb.build_pair(unit_id, out, unit)
            loaded[(unit_id, unit, "pass")] = ifcopenshell.open(str(pair.pass_path))
            loaded[(unit_id, unit, "fail")] = ifcopenshell.open(str(pair.fail_path))
    return loaded


def by_name(model, name):
    [el] = [e for e in model.by_type("IfcRoot") if e.Name == name]
    return el


@pytest.mark.parametrize("unit", ["mm", "m"])
@pytest.mark.parametrize("kind, expected", [("pass", 1.8), ("fail", 1.68)])
def test_space_floor_area_is_square_metres_in_any_project_unit(models, unit, kind, expected):
    model = models[(AREA, unit, kind)]
    assert h.space_floor_area_m2(model, by_name(model, "space_under_test")) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("unit", ["mm", "m"])
@pytest.mark.parametrize("kind, expected", [("pass", 2.75), ("fail", 2.6)])
def test_element_height_is_metres_in_any_project_unit(models, unit, kind, expected):
    model = models[(HEIGHT, unit, kind)]
    assert h.element_height_m(model, by_name(model, "space_under_test")) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("unit", ["mm", "m"])
@pytest.mark.parametrize("kind, expected", [("pass", 1.0), ("fail", 0.9)])
def test_stair_flight_width_is_metres_in_any_project_unit(models, unit, kind, expected):
    model = models[(STAIR, unit, kind)]
    assert h.stair_flight_width_m(model, by_name(model, "flight_under_test")) == pytest.approx(expected, abs=1e-9)


def test_declared_quantity_is_si_or_none(models):
    for unit in ("mm", "m"):
        model = models[(AREA, unit, "pass")]
        space = by_name(model, "space_under_test")
        assert h.declared_quantity(model, space, "Qto_SpaceBaseQuantities", "NetFloorArea") == pytest.approx(1.8)
        assert h.declared_quantity(model, space, "Qto_SpaceBaseQuantities", "GrossFloorArea") is None
        assert h.declared_quantity(model, space, "Qto_Nope", "NetFloorArea") is None


def test_declared_length_is_converted_to_metres():
    f, storey = new_model("x", "mm")
    door = run(f, "root.create_entity", ifc_class="IfcDoor", name="d")
    qto = run(f, "pset.add_qto", product=door, name="Qto_DoorBaseQuantities")
    run(f, "pset.edit_qto", qto=qto, properties={"Width": 900.0})
    assert h.declared_quantity(f, door, "Qto_DoorBaseQuantities", "Width") == pytest.approx(0.9)


def test_helpers_return_none_instead_of_guessing(models):
    f, storey = new_model("x", "mm")
    bare = gb.add_space(f, storey, "no geometry", category="Bathroom", size_x_m=None, size_y_m=None, height_m=None)
    assert h.space_floor_area_m2(f, bare) is None and h.element_height_m(f, bare) is None
    flight = gb.add_stair_flight(f, storey, "no geometry flight", width_m=None)
    assert h.stair_flight_width_m(f, flight) is None
    assert h.pset_value(f, bare, "Pset_SpaceCommon", "Missing") is None
    assert h.building_occupancy(f, flight) is None  # building declares no OccupancyType
    assert h.stair_flight_width_m(f, None) is None and h.space_floor_area_m2(f, None) is None


def test_selection_data_helpers(models):
    model = models[(STAIR, "mm", "pass")]
    assert h.building_occupancy(model, by_name(model, "flight_under_test")) == "Residential"
    assert h.building_occupancy(model, by_name(model, "control_flight")) == "Commercial"
    area = models[(AREA, "mm", "pass")]
    assert h.pset_value(area, by_name(area, "space_under_test"), "Pset_SpaceCommon", "Category") == "Bathroom"
    assert [h.name(e) for e in h.elements(area, "IfcSpace")] == ["space_under_test", "control_store"]
    assert h.elements(area, "IfcDoor") == []


def test_finding_dict_is_validated():
    f = h.finding(type("E", (), {"GlobalId": "g"})(), "fail", "too small", measured=1.0, required=1.8)
    assert f == {"global_id": "g", "verdict": "fail", "detail": "too small", "measured": 1.0, "required": 1.8}
    assert h.validate_finding(f) is None
    for bad in ({**f, "verdict": "passed"}, {**f, "detail": 3}, {**f, "measured": "x"}, {"global_id": "g"},
                {**f, "extra": 1}, "not a dict"):
        assert h.validate_finding(bad) is not None


def test_public_helpers_are_the_documented_surface():
    assert {s.name for s in h.signatures()} == {
        "elements", "name", "pset_value", "declared_quantity", "building_occupancy", "space_floor_area_m2",
        "element_height_m", "stair_flight_width_m", "finding"}
    assert all(s.doc for s in h.signatures())


def test_pilot_fixture_guids_match_expected(models):
    for unit_id in gb.UNITS:
        model = models[(unit_id, "mm", "fail")]
        assert by_name(model, gb.UNDER_TEST[unit_id]).GlobalId == guid(gb.UNDER_TEST[unit_id])
