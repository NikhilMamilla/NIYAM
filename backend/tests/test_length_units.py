"""Regression tests for the millimetre double-scale bug (STATUS.md, fixed on branch fix-mm-units).

The older helper tests build their models with the same fixture builder the helpers were wrong against, so a
mistake in both cancelled out. These models are written by hand with plain IFC entities, the way an authoring tool
writes them: a millimetre project stores 2000 mm as 2000.0. Nothing here goes through ifcopenshell.api, which
converts units itself."""

import ifcopenshell
import ifcopenshell.guid
import pytest

from app.fixtures import geo_builders as gb
from app.geometry import helpers as h

SCALE = {"mm": 1000.0, "m": 1.0}
PREFIX = {"mm": "MILLI", "m": None}


def _project(unit):
    f = ifcopenshell.file(schema="IFC4")
    units = f.createIfcUnitAssignment([f.createIfcSIUnit(None, "LENGTHUNIT", PREFIX[unit], "METRE")])
    origin = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None)
    ctx = f.createIfcGeometricRepresentationContext(None, "Model", 3, 1.0e-5, origin, None)
    body = f.createIfcGeometricRepresentationSubContext("Body", "Model", None, None, None, None, ctx, None,
                                                         "MODEL_VIEW", None)
    f.createIfcProject(ifcopenshell.guid.new(), None, "units", None, None, None, None, [ctx], units)
    return f, body, origin


def _prism(f, body, origin, x_m, y_m, depth_m, unit):
    """A rectangle x_m by y_m extruded depth_m upwards, its corner at the origin, written in the project unit."""
    k = SCALE[unit]
    centre = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((x_m * k / 2, y_m * k / 2)), None)
    profile = f.createIfcRectangleProfileDef("AREA", None, centre, x_m * k, y_m * k)
    solid = f.createIfcExtrudedAreaSolid(profile, origin, f.createIfcDirection((0.0, 0.0, 1.0)), depth_m * k)
    shape = f.createIfcProductDefinitionShape(None, None, [f.createIfcShapeRepresentation(body, "Body", "SweptSolid",
                                                                                        [solid])])
    return f.createIfcLocalPlacement(None, origin), shape


def room(unit):
    """A 2.0 m x 1.2 m room, 2.75 m high: 2.4 m2."""
    f, body, origin = _project(unit)
    placement, shape = _prism(f, body, origin, 2.0, 1.2, 2.75, unit)
    space = f.createIfcSpace(ifcopenshell.guid.new(), None, "room", None, None, placement, shape, None, "ELEMENT",
                             None, None)
    return f, space


def flight(unit):
    """A stair flight with a 3.0 m run along local X, 1.0 m wide along local Y, rising 1.5 m."""
    f, body, origin = _project(unit)
    placement, shape = _prism(f, body, origin, 3.0, 1.0, 1.5, unit)
    return f, f.createIfcStairFlight(ifcopenshell.guid.new(), None, "flight", None, None, placement, shape, None,
                                     None, None, None, None, "STRAIGHT")


@pytest.mark.parametrize("unit", ["mm", "m"])
def test_room_area_and_height_of_an_independently_written_model(unit):
    f, space = room(unit)
    assert h.space_floor_area_m2(f, space) == pytest.approx(2.4, rel=1e-9)
    assert h.element_height_m(f, space) == pytest.approx(2.75, rel=1e-9)


@pytest.mark.parametrize("unit", ["mm", "m"])
def test_stair_flight_width_of_an_independently_written_model(unit):
    f, element = flight(unit)
    assert h.stair_flight_width_m(f, element) == pytest.approx(1.0, rel=1e-9)


def test_millimetre_and_metre_projects_give_the_same_values():
    (fmm, smm), (fm, sm) = room("mm"), room("m")
    assert h.space_floor_area_m2(fmm, smm) == pytest.approx(h.space_floor_area_m2(fm, sm), rel=1e-12)
    assert h.element_height_m(fmm, smm) == pytest.approx(h.element_height_m(fm, sm), rel=1e-12)


@pytest.mark.parametrize("unit", ["mm", "m"])
def test_fixture_builder_writes_shapes_in_the_project_unit(unit, tmp_path):
    """The builder half of the bug: a 2.75 m room in a millimetre file is stored as 2750, not 2 750 000."""
    pair = gb.build_pair("MBBL2016-4.3.1.1#1", tmp_path, unit)
    f = ifcopenshell.open(str(pair.pass_path))
    [space] = [s for s in f.by_type("IfcSpace") if s.Name == "space_under_test"]
    [solid] = space.Representation.Representations[0].Items
    coords = [c for point in solid.SweptArea.OuterCurve.Points.CoordList for c in point]
    assert solid.Depth == pytest.approx(2.75 * SCALE[unit])
    assert max(coords) == pytest.approx(3.5 * SCALE[unit])  # the room is 3.0 m x 3.5 m
