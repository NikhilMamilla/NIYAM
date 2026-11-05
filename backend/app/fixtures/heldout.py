"""Held-out fixtures for the six pilot units: scored by the evaluation harness, never seen by the gate or a prompt.

Values, element names and (for quantitative rules) the project length unit differ from the dev pairs, and every
quantitative unit has a boundary pair: exactly the threshold must PASS, just under it must FAIL. The expected
verdicts below are written by hand from the clause text; nothing is derived by running a rule.
Verdicts: "pass" (the rule applies and is met), "fail" (violation), "out_of_scope" (the rule does not apply)."""

import json
from pathlib import Path

from app.fixtures import geo_builders as gb
from app.fixtures.builders import REPO_ROOT, _stabilise, add_door, guid, new_model, safe_name

HELDOUT_DIR = REPO_ROOT / "fixtures" / "heldout"
DOOR_HEIGHT_M = 2.2

# door: (name, fire_exit, operation type, width m, expected); dev door fixtures are in mm, these are in metres
DOOR_UNITS = {
    "MBBL2016-5.4.2#1": {  # revolving door shall not be a means of fire exit
        "pass": [("HO exit swing right", True, "SINGLE_SWING_RIGHT", 1.1, "pass"),
                 ("HO exit double swing", True, "DOUBLE_DOOR_DOUBLE_SWING", 1.6, "pass"),
                 ("HO revolving lobby door", False, "REVOLVING", 1.8, "out_of_scope")],
        "fail": [("HO revolving exit", True, "REVOLVING", 1.8, "fail"),
                 ("HO exit swing left 1.2 m", True, "SINGLE_SWING_LEFT", 1.2, "pass"),
                 ("HO revolving lobby door", False, "REVOLVING", 1.8, "out_of_scope")],
    },
    "MBBL2016-5.4.1#b": {  # no exit doorway less than 1 m wide
        "pass": [("HO exit exactly 1.0 m", True, "SINGLE_SWING_LEFT", 1.0, "pass"),  # boundary: >= passes
                 ("HO exit 1.25 m", True, "DOUBLE_DOOR_DOUBLE_SWING", 1.25, "pass"),
                 ("HO store door 0.6 m", False, "SINGLE_SWING_RIGHT", 0.6, "out_of_scope")],
        "fail": [("HO exit 0.99 m", True, "SINGLE_SWING_LEFT", 0.99, "fail"),  # just under the bound
                 ("HO exit 1.5 m", True, "DOUBLE_DOOR_DOUBLE_SWING", 1.5, "pass"),
                 ("HO store door 0.8 m", False, "SINGLE_SWING_RIGHT", 0.8, "out_of_scope")],
    },
    "MBBL2016-5.4.1#c": {  # overhead or sliding doors shall not be installed (on exits)
        "pass": [("HO exit swing left", True, "SINGLE_SWING_LEFT", 1.1, "pass"),
                 ("HO exit double swing", True, "DOUBLE_DOOR_SINGLE_SWING", 1.6, "pass"),
                 ("HO sliding wardrobe door", False, "SLIDING_TO_RIGHT", 1.2, "out_of_scope")],
        "fail": [("HO overhead exit", True, "ROLLINGUP", 2.4, "fail"),
                 ("HO double sliding exit", True, "DOUBLE_DOOR_SLIDING", 1.6, "fail"),
                 ("HO exit swing left", True, "SINGLE_SWING_LEFT", 1.1, "pass")],
    },
}
# space: (name, category, x m, y m, height m, expected); dev geometric pairs are in mm, these are in metres
SPACE_UNITS = {
    "MBBL2016-4.5.2#1": {  # bathroom area not less than 1.8 m2
        "pass": [("HO bath exactly 1.8 m2", "Bathroom", 1.5, 1.2, 2.6, "pass"),  # boundary
                 ("HO bath 2.6 m2", "Bathroom", 2.0, 1.3, 2.6, "pass"),
                 ("HO small habitable 1.0 m2", "Habitable", 1.0, 1.0, 2.8, "out_of_scope")],
        "fail": [("HO bath 1.79 m2", "Bathroom", 1.79 / 1.2, 1.2, 2.6, "fail"),  # just under
                 ("HO bath 2.0 m2", "Bathroom", 2.0, 1.0, 2.6, "pass"),
                 ("HO store 0.9 m2", "Store", 0.9, 1.0, 2.6, "out_of_scope")],
    },
    "MBBL2016-4.3.1.1#1": {  # habitable room height not less than 2.75 m
        "pass": [("HO bedroom exactly 2.75 m", "Habitable", 3.2, 3.0, 2.75, "pass"),  # boundary
                 ("HO hall 3.1 m", "Habitable", 4.0, 3.5, 3.1, "pass"),
                 ("HO store 2.2 m", "Store", 1.5, 1.5, 2.2, "out_of_scope"),
                 ("HO bath 2.4 m", "Bathroom", 1.5, 1.5, 2.4, "out_of_scope")],
        "fail": [("HO bedroom 2.74 m", "Habitable", 3.2, 3.0, 2.74, "fail"),  # just under
                 ("HO study 2.9 m", "Habitable", 2.8, 2.5, 2.9, "pass"),
                 ("HO store 2.0 m", "Store", 1.5, 1.5, 2.0, "out_of_scope")],
    },
}
# flight: (name, building occupancy, width m, expected)
STAIR_UNITS = {
    "MBBL2016-4.17.2#A": {  # residential staircase width 1.0 m
        "pass": [("HO flight exactly 1.0 m", "Residential", 1.0, "pass"),  # boundary
                 ("HO flight 1.3 m", "Residential", 1.3, "pass"),
                 ("HO office flight 0.85 m", "Commercial", 0.85, "out_of_scope")],
        "fail": [("HO flight 0.99 m", "Residential", 0.99, "fail"),  # just under
                 ("HO flight 1.2 m", "Residential", 1.2, "pass"),
                 ("HO office flight 0.7 m", "Commercial", 0.7, "out_of_scope")],
    },
}
UNITS = [*DOOR_UNITS, *SPACE_UNITS, *STAIR_UNITS]


def _model(unit_id: str, kind: str):
    f, storey = new_model(f"NIYAM held-out {unit_id} {kind}", length_unit="m")
    rows, names = [], set()
    if unit_id in DOOR_UNITS:
        for name, fire_exit, op, width, expected in DOOR_UNITS[unit_id][kind]:
            add_door(f, storey, name, fire_exit=fire_exit, operation_type=op, width=width, height=DOOR_HEIGHT_M)
            rows.append((name, expected))
    elif unit_id in SPACE_UNITS:
        x = 0.0
        for name, category, sx, sy, height, expected in SPACE_UNITS[unit_id][kind]:
            gb.add_space(f, storey, name, category=category, size_x_m=sx, size_y_m=sy, height_m=height, x_m=x)
            x += sx + 0.5
            rows.append((name, expected))
    else:
        building = storey.Decomposes[0].RelatingObject
        gb.set_occupancy(f, building, "Residential")
        storeys, x = {"Residential": storey}, 0.0
        for name, occupancy, width, expected in STAIR_UNITS[unit_id][kind]:
            if occupancy not in storeys:
                storeys[occupancy] = gb.add_control_building(f, building, f"{occupancy} annex", occupancy)
            gb.add_stair_flight(f, storeys[occupancy], name, width_m=width, x_m=x)
            x += 4.0
            rows.append((name, expected))
    names = frozenset(n for n, _ in rows)
    _stabilise(f, f"heldout/{unit_id}/{kind}", keep_names=names)
    return f, rows


def all_units(root: Path = HELDOUT_DIR) -> list[str]:
    """Every unit with a held-out set: the six hand-written ones and all spec-generated ones."""
    return sorted(json.loads(p.read_text(encoding="utf-8"))["unit_id"] for p in root.glob("*.truth.json"))


def paths(unit_id: str, root: Path = HELDOUT_DIR) -> dict[str, Path]:
    name = safe_name(unit_id)
    return {"pass": root / f"{name}__heldout_pass.ifc", "fail": root / f"{name}__heldout_fail.ifc",
            "truth": root / f"{name}.truth.json"}


def build(unit_id: str, root: Path = HELDOUT_DIR) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    out = paths(unit_id, root)
    truth = {"unit_id": unit_id, "length_unit": "m", "synthetic": True, "models": {}}
    for kind in ("pass", "fail"):
        f, rows = _model(unit_id, kind)
        f.write(str(out[kind]))
        truth["models"][out[kind].name] = [{"name": n, "global_id": guid(n), "expected": e} for n, e in rows]
    out["truth"].write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    return out


def build_all(root: Path = HELDOUT_DIR) -> list[dict[str, Path]]:
    return [build(u, root) for u in UNITS]


def load_truth(unit_id: str, root: Path = HELDOUT_DIR) -> dict:
    return json.loads(paths(unit_id, root)["truth"].read_text(encoding="utf-8"))
