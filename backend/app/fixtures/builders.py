"""Deterministic tiny IFC4 fixture models for pilot rule units (millimetre project units)."""

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "fixtures" / "ifc"
TIMESTAMP = "2026-01-01T00:00:00"
GUID_NAMESPACE = uuid.UUID("6f1c2a9e-4d1b-4f0e-9a51-3c1d1f0a7e11")
DOOR_UNDER_TEST = "door_under_test"


@dataclass(frozen=True)
class FixturePair:
    pass_path: Path
    fail_path: Path
    expected_failing: frozenset[str]  # GlobalIds the rule must flag in the fail fixture


def safe_name(unit_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "_", unit_id)


def guid(key: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(GUID_NAMESPACE, key).hex)


def run(f, usecase, **kwargs):
    return ifcopenshell.api.run(usecase, f, **kwargs)


def new_model(name: str, length_unit: str = "mm"):
    f = ifcopenshell.file(schema="IFC4")
    f.header.file_name.time_stamp = TIMESTAMP
    project = run(f, "root.create_entity", ifc_class="IfcProject", name=name)
    if length_unit == "mm":
        run(f, "unit.assign_unit")  # millimetres, as most Indian BIM authoring does
    elif length_unit == "m":
        run(f, "unit.assign_unit", units=[run(f, "unit.add_si_unit", unit_type="LENGTHUNIT")])
    else:
        raise ValueError(f"length_unit must be 'mm' or 'm', not {length_unit!r}")
    parent = project
    for ifc_class in ("IfcSite", "IfcBuilding", "IfcBuildingStorey"):
        child = run(f, "root.create_entity", ifc_class=ifc_class, name=ifc_class[3:])
        run(f, "aggregate.assign_object", products=[child], relating_object=parent)
        parent = child
    return f, parent


def add_storey(f, building_storey, name: str):
    building = building_storey.Decomposes[0].RelatingObject
    storey = run(f, "root.create_entity", ifc_class="IfcBuildingStorey", name=name)
    run(f, "aggregate.assign_object", products=[storey], relating_object=building)
    return storey


def add_door(f, storey, name, *, fire_exit, operation_type="SINGLE_SWING_LEFT", width=1000.0, height=2100.0):
    """width/height are in project length units. fire_exit=None omits Pset_DoorCommon; width=None omits
    the width (OverallWidth and Qto_DoorBaseQuantities.Width)."""
    door = run(f, "root.create_entity", ifc_class="IfcDoor", name=name)
    door.GlobalId = guid(name)  # same GlobalId in pass and fail fixtures
    door.OperationType = operation_type
    door.OverallWidth, door.OverallHeight = width, height
    run(f, "spatial.assign_container", products=[door], relating_structure=storey)
    if fire_exit is not None:
        pset = run(f, "pset.add_pset", product=door, name="Pset_DoorCommon")
        run(f, "pset.edit_pset", pset=pset, properties={"FireExit": fire_exit})
    qto = run(f, "pset.add_qto", product=door, name="Qto_DoorBaseQuantities")
    quantities = {"Height": height} if width is None else {"Width": width, "Height": height}
    run(f, "pset.edit_qto", qto=qto, properties=quantities)
    return door


# unit id -> (door-under-test kwargs for the pass fixture, for the fail fixture, control door kwargs).
# The control door is not a fire exit: an over-broad spec that ignores the FireExit applicability
# fails it in the pass fixture.
PILOTS = {
    "MBBL2016-5.4.2#1": (
        {"operation_type": "SINGLE_SWING_LEFT"},
        {"operation_type": "REVOLVING"},
        {"operation_type": "REVOLVING"},
    ),
    "MBBL2016-5.4.1#b": (
        {"width": 1000.0},  # exactly at the bound: "not less than" is inclusive
        {"width": 900.0},
        {"width": 750.0},  # bathroom-type door, allowed 0.75 m by the same sub-item
    ),
    "MBBL2016-5.4.1#c": (
        {"operation_type": "SINGLE_SWING_RIGHT"},
        {"operation_type": "SLIDING_TO_LEFT"},
        {"operation_type": "SLIDING_TO_LEFT"},
    ),
}
PILOT_UNITS = list(PILOTS)


def _stabilise(f, key: str, keep_names: frozenset[str] = frozenset()) -> None:
    """Make output byte-reproducible: fixed GlobalIds and sorted set-valued aggregates."""
    for entity in f.by_type("IfcRoot"):
        if not entity.is_a("IfcDoor") and entity.Name not in keep_names:  # these keep name-based ids
            entity.GlobalId = guid(f"{key}/#{entity.id()}")
    for ua in f.by_type("IfcUnitAssignment"):
        ua.Units = sorted(ua.Units, key=lambda e: e.id())
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        rel.RelatedElements = sorted(rel.RelatedElements, key=lambda e: e.id())
    for rel in f.by_type("IfcRelAggregates"):
        rel.RelatedObjects = sorted(rel.RelatedObjects, key=lambda e: e.id())


def build_pair(unit_id: str, out_dir: Path) -> FixturePair:
    pass_kwargs, fail_kwargs, control_kwargs = PILOTS[unit_id]
    paths = {}
    for kind, kwargs in (("pass", pass_kwargs), ("fail", fail_kwargs)):
        f, storey = new_model(f"NIYAM fixture {unit_id}")
        add_door(f, storey, DOOR_UNDER_TEST, fire_exit=True, **kwargs)
        add_door(f, storey, "control_non_exit_door", fire_exit=False, **control_kwargs)
        _stabilise(f, unit_id)
        paths[kind] = out_dir / f"{safe_name(unit_id)}__{kind}.ifc"
        f.write(str(paths[kind]))
    return FixturePair(paths["pass"], paths["fail"], frozenset({guid(DOOR_UNDER_TEST)}))


def build_all(out_dir: Path = FIXTURES_DIR) -> list[FixturePair]:
    from app.fixtures import geo_builders  # imports this module, so it is loaded lazily

    out_dir.mkdir(parents=True, exist_ok=True)
    return [build_pair(unit_id, out_dir) for unit_id in PILOT_UNITS] + [
        geo_builders.build_pair(unit_id, out_dir, unit) for unit_id in geo_builders.UNITS for unit in ("mm", "m")]


def fixture_pair(unit_id: str, fixtures_dir: Path = FIXTURES_DIR, length_unit: str = "mm") -> FixturePair:
    from app.fixtures import geo_builders

    if unit_id in geo_builders.VALUES:
        return geo_builders.pair_paths(unit_id, fixtures_dir, length_unit)
    if unit_id not in PILOTS:
        raise KeyError(f"no fixtures defined for {unit_id}")
    name = safe_name(unit_id)
    return FixturePair(
        fixtures_dir / f"{name}__pass.ifc", fixtures_dir / f"{name}__fail.ifc", frozenset({guid(DOOR_UNDER_TEST)})
    )
