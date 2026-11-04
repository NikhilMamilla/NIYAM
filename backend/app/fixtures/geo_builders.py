"""Deterministic fixtures for the geometric pilot units: spaces and stair flights with real extruded geometry.

Each unit has a pass/fail pair that differs only in the value the rule bounds, plus an out-of-scope control
element. Every pair exists in a millimetre and a metre project (`..._m.ifc`)."""

from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit
import numpy as np

from app.fixtures.builders import FixturePair, _stabilise, guid, new_model, run, safe_name

UNDER_TEST = {
    "MBBL2016-4.5.2#1": "space_under_test",
    "MBBL2016-4.3.1.1#1": "space_under_test",
    "MBBL2016-4.17.2#A": "flight_under_test",
}
VALUES = {  # (pass, fail): the quantity the rule bounds, in metres or square metres
    "MBBL2016-4.5.2#1": (1.8, 1.68),  # bathroom floor area: exactly the bound / 1.4 m x 1.2 m
    "MBBL2016-4.3.1.1#1": (2.75, 2.6),  # habitable room height
    "MBBL2016-4.17.2#A": (1.0, 0.9),  # residential stair flight width
}
UNITS = list(VALUES)
KEEP_NAMES = frozenset({"space_under_test", "flight_under_test", "control_store", "control_flight"})


def _body_context(f):
    body = [c for c in f.by_type("IfcGeometricRepresentationSubContext") if c.ContextIdentifier == "Body"]
    if body:
        return body[0]
    parent = run(f, "context.add_context", context_type="Model")
    return run(f, "context.add_context", context_type="Model", context_identifier="Body",
               target_view="MODEL_VIEW", parent=parent)


def _prism(f, product, size_x_m: float, size_y_m: float, height_m: float, x_m: float) -> None:
    """Extruded rectangle (size_x x size_y metres, height_m tall) with its corner x_m along X."""
    k = 1.0 / ifcopenshell.util.unit.calculate_unit_scale(f)  # metres -> project length unit
    poly = [(0.0, 0.0), (size_x_m * k, 0.0), (size_x_m * k, size_y_m * k), (0.0, size_y_m * k)]
    rep = run(f, "geometry.add_slab_representation", context=_body_context(f), depth=height_m * k, polyline=poly)
    run(f, "geometry.assign_representation", product=product, representation=rep)
    matrix = np.eye(4)
    matrix[0, 3] = x_m
    run(f, "geometry.edit_object_placement", product=product, matrix=matrix)


def add_space(f, parent, name, *, category, size_x_m, size_y_m, height_m, x_m=0.0, declared_area_m2=None):
    """An IfcSpace shaped as an extruded rectangle. category=None omits Pset_SpaceCommon; size_x_m=None gives the
    space no geometry (it exists, but nothing can be computed from it)."""
    space = run(f, "root.create_entity", ifc_class="IfcSpace", name=name)
    space.GlobalId = guid(name)  # same id in pass and fail
    run(f, "aggregate.assign_object", products=[space], relating_object=parent)
    if size_x_m is not None:
        _prism(f, space, size_x_m, size_y_m, height_m, x_m)
    if category is not None:
        pset = run(f, "pset.add_pset", product=space, name="Pset_SpaceCommon")
        run(f, "pset.edit_pset", pset=pset, properties={"Category": category})
    if declared_area_m2 is not None:
        qto = run(f, "pset.add_qto", product=space, name="Qto_SpaceBaseQuantities")
        run(f, "pset.edit_qto", qto=qto, properties={"NetFloorArea": declared_area_m2})
    return space


def add_stair_flight(f, storey, name, *, width_m, run_m=3.0, rise_m=1.5, x_m=0.0):
    """An IfcStairFlight shaped as a prism: run along local X, width along local Y. width_m=None: no geometry."""
    flight = run(f, "root.create_entity", ifc_class="IfcStairFlight", name=name)
    flight.GlobalId = guid(name)
    run(f, "spatial.assign_container", products=[flight], relating_structure=storey)
    if width_m is not None:
        _prism(f, flight, run_m, width_m, rise_m, x_m)
    return flight


def set_occupancy(f, building, occupancy: str) -> None:
    pset = run(f, "pset.add_pset", product=building, name="Pset_BuildingCommon")
    run(f, "pset.edit_pset", pset=pset, properties={"OccupancyType": occupancy})


def add_control_building(f, building, name, occupancy):
    """A second building (own storey) so a control stair can sit in a different occupancy."""
    other = run(f, "root.create_entity", ifc_class="IfcBuilding", name=name)
    run(f, "aggregate.assign_object", products=[other], relating_object=building.Decomposes[0].RelatingObject)
    if occupancy is not None:
        set_occupancy(f, other, occupancy)
    storey = run(f, "root.create_entity", ifc_class="IfcBuildingStorey", name=f"{name} storey")
    run(f, "aggregate.assign_object", products=[storey], relating_object=other)
    return storey


def _build_model(unit_id: str, value: float, length_unit: str):
    f, storey = new_model(f"NIYAM fixture {unit_id}", length_unit=length_unit)
    building = storey.Decomposes[0].RelatingObject
    if unit_id == "MBBL2016-4.5.2#1":
        add_space(f, storey, "space_under_test", category="Bathroom", size_x_m=value / 1.2, size_y_m=1.2,
                  height_m=2.75, declared_area_m2=value)
        add_space(f, storey, "control_store", category="Store", size_x_m=1.0, size_y_m=1.0, height_m=2.75,
                  x_m=5.0, declared_area_m2=1.0)  # too small for a bathroom, but not a bathroom
    elif unit_id == "MBBL2016-4.3.1.1#1":
        add_space(f, storey, "space_under_test", category="Habitable", size_x_m=3.0, size_y_m=3.5,
                  height_m=value, declared_area_m2=10.5)
        add_space(f, storey, "control_store", category="Store", size_x_m=2.0, size_y_m=2.0, height_m=2.0,
                  x_m=5.0, declared_area_m2=4.0)
    else:
        set_occupancy(f, building, "Residential")
        add_stair_flight(f, storey, "flight_under_test", width_m=value)
        control = add_control_building(f, building, "Control building", "Commercial")
        add_stair_flight(f, control, "control_flight", width_m=0.8, x_m=5.0)  # narrow, but not residential
    return f


def build_pair(unit_id: str, out_dir: Path, length_unit: str = "mm") -> FixturePair:
    suffix = "" if length_unit == "mm" else f"_{length_unit}"
    paths = {}
    for kind, value in zip(("pass", "fail"), VALUES[unit_id]):
        f = _build_model(unit_id, value, length_unit)
        _stabilise(f, unit_id, keep_names=KEEP_NAMES)
        paths[kind] = out_dir / f"{safe_name(unit_id)}__{kind}{suffix}.ifc"
        f.write(str(paths[kind]))
    return FixturePair(paths["pass"], paths["fail"], frozenset({guid(UNDER_TEST[unit_id])}))


def pair_paths(unit_id: str, fixtures_dir: Path, length_unit: str = "mm") -> FixturePair:
    suffix = "" if length_unit == "mm" else f"_{length_unit}"
    name = safe_name(unit_id)
    return FixturePair(fixtures_dir / f"{name}__pass{suffix}.ifc", fixtures_dir / f"{name}__fail{suffix}.ifc",
                       frozenset({guid(UNDER_TEST[unit_id])}))
