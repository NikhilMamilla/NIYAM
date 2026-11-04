"""Synthetic two-storey sample buildings with hand-written ground truth for the v0 rulepack.

These are NOT real Indian buildings: they only seed the door cases the pilot rules distinguish.
Expected verdicts are written by hand per door and rule, independently of the audit engine."""

import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.unit
import numpy as np

from app.fixtures import geo_builders
from app.fixtures.builders import REPO_ROOT, TIMESTAMP, _stabilise, add_door, add_storey, guid, new_model, run

SAMPLES_DIR = REPO_ROOT / "fixtures" / "samples"
RULES = ("MBBL2016-5.4.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.1#c")
CODE = {"P": "passed", "F": "failed", "U": "unchecked", "O": "out_of_scope"}

# name, storey, FireExit (None = no Pset_DoorCommon), OperationType, width in metres (None = no width),
# expected verdicts for (5.4.2#1 no revolving exits, 5.4.1#b exit width >= 1 m, 5.4.1#c no sliding/overhead exits)
SAMPLE_A = [
    ("A-G-01 main exit", 0, True, "DOUBLE_DOOR_DOUBLE_SWING", 1.8, "PPP"),
    ("A-G-02 side exit at 1.0 m", 0, True, "SINGLE_SWING_LEFT", 1.0, "PPP"),
    ("A-G-03 narrow exit", 0, True, "SINGLE_SWING_RIGHT", 0.9, "PFP"),
    ("A-G-04 revolving exit", 0, True, "REVOLVING", 1.2, "FPP"),
    ("A-G-05 sliding exit", 0, True, "SLIDING_TO_LEFT", 1.2, "PPF"),
    ("A-G-06 revolving lobby door (not exit)", 0, False, "REVOLVING", 0.75, "OOO"),
    ("A-1-01 rolling shutter exit", 1, True, "ROLLINGUP", 1.5, "PPF"),
    ("A-1-02 narrow sliding exit", 1, True, "DOUBLE_DOOR_SLIDING", 0.8, "PFF"),
    ("A-1-03 sliding store door (not exit)", 1, False, "SLIDING_TO_RIGHT", 0.7, "OOO"),
    ("A-1-04 door without FireExit", 1, None, "SINGLE_SWING_LEFT", 0.9, "UUU"),
    ("A-1-05 revolving door without FireExit", 1, None, "REVOLVING", 1.2, "UUU"),
    ("A-1-06 exit without width quantity", 1, True, "SINGLE_SWING_LEFT", None, "PUP"),
]
SAMPLE_B = [
    ("B-G-01 main exit", 0, True, "SINGLE_SWING_LEFT", 1.1, "PPP"),
    ("B-G-02 narrow exit", 0, True, "SINGLE_SWING_RIGHT", 0.95, "PFP"),
    ("B-G-03 revolving exit", 0, True, "REVOLVING", 1.0, "FPP"),
    ("B-G-04 sliding exit", 0, True, "SLIDING_TO_RIGHT", 1.0, "PPF"),
    ("B-G-05 revolving door (not exit)", 0, False, "REVOLVING", 0.8, "OOO"),
    ("B-1-01 overhead exit", 1, True, "ROLLINGUP", 2.0, "PPF"),
    ("B-1-02 stair exit", 1, True, "SINGLE_SWING_LEFT", 1.0, "PPP"),
    ("B-1-03 sliding cupboard door (not exit)", 1, False, "DOUBLE_DOOR_SLIDING", 0.6, "OOO"),
    ("B-1-04 door without FireExit", 1, None, "SINGLE_SWING_LEFT", 1.0, "UUU"),
    ("B-1-05 sliding door without FireExit", 1, None, "SLIDING_TO_LEFT", 0.9, "UUU"),
]
# No door declares FireExit: nothing can be checked, so the audit must be "incomplete", never "compliant".
SAMPLE_C = [
    ("C-G-01 entrance door", 0, None, "SINGLE_SWING_LEFT", 1.2, "UUU"),
    ("C-G-02 revolving entrance", 0, None, "REVOLVING", 2.0, "UUU"),
    ("C-1-01 corridor door", 1, None, "SINGLE_SWING_RIGHT", 0.9, "UUU"),
    ("C-1-02 sliding door", 1, None, "SLIDING_TO_LEFT", 1.0, "UUU"),
]
SAMPLES = {
    "sample_a_mm": ("mm", SAMPLE_A, "noncompliant"),
    "sample_b_m": ("m", SAMPLE_B, "noncompliant"),
    "sample_c_no_fireexit_mm": ("mm", SAMPLE_C, "incomplete"),
}
# Geometric samples: rooms and stair flights, no doors. Spaces: name, Pset_SpaceCommon.Category (None = not
# declared), body geometry as (x, y, height) in metres (None = no geometry), expected verdicts for
# (4.5.2#1 bathroom area >= 1.8 m2, 4.3.1.1#1 habitable room height >= 2.75 m). Flights: name, occupancy of
# their building (None = not declared), width in metres (None = no geometry), expected verdict for 4.17.2#A
# (residential stair width >= 1.0 m).
GEO_RULES = ("MBBL2016-4.5.2#1", "MBBL2016-4.3.1.1#1")
STAIR_RULE = "MBBL2016-4.17.2#A"
SAMPLE_D = (
    [("D-B-01 bathroom 2.4 m2", "Bathroom", (2.0, 1.2, 2.75), "PO"),
     ("D-B-02 small bathroom 1.5 m2", "Bathroom", (1.25, 1.2, 2.75), "FO"),
     ("D-B-03 bathroom exactly 1.8 m2", "Bathroom", (1.5, 1.2, 2.75), "PO"),
     ("D-B-04 bathroom without geometry", "Bathroom", None, "UO"),
     ("D-H-01 living room 3.0 m high", "Habitable", (4.0, 3.0, 3.0), "OP"),
     ("D-H-02 bedroom 2.5 m high", "Habitable", (3.5, 3.0, 2.5), "OF"),
     ("D-H-03 bedroom without geometry", "Habitable", None, "OU"),
     ("D-S-01 store room", "Store", (2.0, 2.0, 2.0), "OO"),
     ("D-X-01 space without category", None, (2.0, 2.0, 2.75), "UU")],
    [("D-ST-01 residential flight 1.2 m", "Residential", 1.2, "P"),
     ("D-ST-02 residential flight 0.9 m", "Residential", 0.9, "F"),
     ("D-ST-03 residential flight without geometry", "Residential", None, "U"),
     ("D-ST-04 commercial flight 0.8 m", "Commercial", 0.8, "O"),
     ("D-ST-05 flight in a building without occupancy", None, 1.1, "U")],
)
SAMPLE_E = (
    [("E-B-01 bathroom 3.0 m2", "Bathroom", (2.5, 1.2, 2.4), "PO"),
     ("E-B-02 bathroom 1.68 m2", "Bathroom", (1.4, 1.2, 2.4), "FO"),
     ("E-B-03 bathroom without geometry", "Bathroom", None, "UO"),
     ("E-H-01 bedroom exactly 2.75 m high", "Habitable", (3.0, 3.5, 2.75), "OP"),
     ("E-H-02 bedroom 2.7 m high", "Habitable", (3.0, 3.0, 2.7), "OF"),
     ("E-H-03 bedroom without geometry", "Habitable", None, "OU"),
     ("E-S-01 store room", "Store", (1.5, 1.5, 2.1), "OO"),
     ("E-X-01 space without category", None, (2.5, 2.0, 2.75), "UU")],
    [("E-ST-01 residential flight exactly 1.0 m", "Residential", 1.0, "P"),
     ("E-ST-02 residential flight 0.85 m", "Residential", 0.85, "F"),
     ("E-ST-03 commercial flight 0.8 m", "Commercial", 0.8, "O"),
     ("E-ST-04 flight in a building without occupancy", None, 1.2, "U")],
)
GEO_SAMPLES = {
    "sample_d_rooms_stairs_mm": ("mm", SAMPLE_D, "noncompliant"),
    "sample_e_rooms_stairs_m": ("m", SAMPLE_E, "noncompliant"),
}
DESCRIPTIONS = {
    "sample_d_rooms_stairs_mm": "Synthetic model in millimetres: 9 spaces and 5 stair flights for the geometric rules.",
    "sample_e_rooms_stairs_m": "Synthetic model in metres: 8 spaces and 4 stair flights for the geometric rules.",
    "sample_a_mm": "Synthetic 2-storey model in millimetres, 12 doors covering every v0 rule case.",
    "sample_b_m": "Synthetic 2-storey model in metres, 10 doors covering every v0 rule case.",
    "sample_c_no_fireexit_mm": "Synthetic model whose 4 doors have no FireExit data: the audit is incomplete.",
}
STOREYS = ("Ground floor", "First floor")
INVALID_DIR = REPO_ROOT / "fixtures" / "invalid"


STOREY_HEIGHT_M, DOOR_SPACING_M, DOOR_HEIGHT_M = 3.5, 2.0, 2.1


def _placement(x: float, z: float) -> np.ndarray:
    matrix = np.eye(4)
    matrix[0, 3], matrix[2, 3] = x, z
    return matrix


def _add_geometry(f, storeys, doors) -> None:
    """Simple boxes so the samples can be viewed in 3D: one per door, one floor slab per storey (SI metres)."""
    model = run(f, "context.add_context", context_type="Model")
    body = run(f, "context.add_context", context_type="Model", context_identifier="Body",
               target_view="MODEL_VIEW", parent=model)
    for level, storey in enumerate(storeys):
        storey.Elevation = level * STOREY_HEIGHT_M / ifcopenshell.util.unit.calculate_unit_scale(f)
        on_level = [d for d in doors if d[1] == level]
        length = len(on_level) * DOOR_SPACING_M + 1.0
        slab = run(f, "root.create_entity", ifc_class="IfcSlab", name=f"{storey.Name} slab")
        run(f, "spatial.assign_container", products=[slab], relating_structure=storey)
        run(f, "geometry.assign_representation", product=slab, representation=run(
            f, "geometry.add_slab_representation", context=body, depth=0.2,
            polyline=[(0.0, -1.5), (length, -1.5), (length, 1.5), (0.0, 1.5)]))
        run(f, "geometry.edit_object_placement", product=slab, matrix=_placement(0.0, level * STOREY_HEIGHT_M - 0.2))
        for i, (door_name, _, _, _, width_m, _) in enumerate(on_level):
            door = f.by_guid(guid(door_name))
            run(f, "geometry.assign_representation", product=door, representation=run(
                f, "geometry.add_wall_representation", context=body, length=width_m or 0.9,
                height=DOOR_HEIGHT_M, thickness=0.1))
            run(f, "geometry.edit_object_placement", product=door,
                matrix=_placement(1.0 + i * DOOR_SPACING_M, level * STOREY_HEIGHT_M))


def build_sample(name: str, out_dir: Path) -> Path:
    unit, doors, expected_status = SAMPLES[name]
    scale = 1000.0 if unit == "mm" else 1.0
    f, ground = new_model(f"NIYAM synthetic {name}", length_unit=unit)
    ground.Name = STOREYS[0]
    storeys = [ground, add_storey(f, ground, STOREYS[1])]
    truth = []
    for door_name, level, fire_exit, op, width_m, codes in doors:
        add_door(f, storeys[level], door_name, fire_exit=fire_exit, operation_type=op,
                 width=None if width_m is None else width_m * scale, height=DOOR_HEIGHT_M * scale)
        truth.append({"name": door_name, "global_id": guid(door_name), "storey": STOREYS[level],
                      "fire_exit": fire_exit, "operation_type": op, "width_m": width_m,
                      "expected": dict(zip(RULES, (CODE[c] for c in codes)))})
    _add_geometry(f, storeys, doors)
    _stabilise(f, name)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.ifc"
    f.write(str(path))
    (out_dir / f"{name}.truth.json").write_text(json.dumps(
        {"sample": name, "synthetic": True, "length_unit": unit, "expected_status": expected_status,
         "doors": truth}, indent=2) + "\n", encoding="utf-8")
    return path


def build_geo_sample(name: str, out_dir: Path) -> Path:
    unit, (spaces, flights), expected_status = GEO_SAMPLES[name]
    f, storey = new_model(f"NIYAM synthetic {name}", length_unit=unit)
    building = storey.Decomposes[0].RelatingObject
    geo_builders.set_occupancy(f, building, "Residential")
    storeys = {"Residential": storey}
    truth_spaces, truth_stairs, x = [], [], 0.0
    for space_name, category, size, codes in spaces:
        sx, sy, height = size or (None, None, None)
        geo_builders.add_space(f, storey, space_name, category=category, size_x_m=sx, size_y_m=sy, height_m=height,
                               x_m=x)
        x += (sx or 2.0) + 0.5
        truth_spaces.append({"name": space_name, "global_id": guid(space_name), "category": category,
                             "size_m": size, "expected": dict(zip(GEO_RULES, (CODE[c] for c in codes)))})
    for flight_name, occupancy, width, code in flights:
        if occupancy not in storeys:  # one extra building per distinct occupancy (None = declares none)
            storeys[occupancy] = geo_builders.add_control_building(f, building, f"{occupancy or 'Unlabelled'} block",
                                                                   occupancy)
        geo_builders.add_stair_flight(f, storeys[occupancy], flight_name, width_m=width, x_m=x)
        x += 3.5
        truth_stairs.append({"name": flight_name, "global_id": guid(flight_name), "building_occupancy": occupancy,
                             "width_m": width, "expected": {STAIR_RULE: CODE[code]}})
    _stabilise(f, name, keep_names=frozenset(s[0] for s in spaces) | frozenset(s[0] for s in flights))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.ifc"
    f.write(str(path))
    (out_dir / f"{name}.truth.json").write_text(json.dumps(
        {"sample": name, "synthetic": True, "length_unit": unit, "expected_status": expected_status,
         "doors": [], "spaces": truth_spaces, "stairs": truth_stairs}, indent=2) + "\n", encoding="utf-8")
    return path


def build_samples(out_dir: Path = SAMPLES_DIR) -> list[Path]:
    return [build_sample(name, out_dir) for name in SAMPLES] + [build_geo_sample(name, out_dir) for name in GEO_SAMPLES]


def build_ifc2x3(out_dir: Path = INVALID_DIR) -> Path:
    """A minimal IFC2X3 file, used to check that non-IFC4 uploads are refused."""
    f = ifcopenshell.file(schema="IFC2X3")
    f.header.file_name.time_stamp = TIMESTAMP
    f.create_entity("IfcProject", GlobalId=guid("ifc2x3 project"), Name="IFC2X3 test project")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "ifc2x3_minimal.ifc"
    f.write(str(path))
    return path
