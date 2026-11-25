"""Helpers that generated geometric checks may call (and nothing else).

Every helper returns SI values (metres, square metres) whatever the project length unit, or None when the value
cannot be computed from the model. Helpers never guess. Unit conversion happens here, once.

A check is `def check(model, helpers) -> list[finding dict]`; `helpers` is the HELPERS object below."""

import inspect
import math
from dataclasses import dataclass
from types import SimpleNamespace

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit

VERDICTS = ("pass", "fail", "unchecked")
FINDING_KEYS = {"global_id", "verdict", "detail", "measured", "required"}
# quantity class -> (value attribute, unit type, power of the length unit)
_QUANTITIES = {
    "IfcQuantityLength": ("LengthValue", "LENGTHUNIT"),
    "IfcQuantityArea": ("AreaValue", "AREAUNIT"),
    "IfcQuantityVolume": ("VolumeValue", "VOLUMEUNIT"),
}


def elements(model, ifc_class):
    """All occurrences of an IFC class (subclasses included), ordered by file id."""
    return sorted(model.by_type(ifc_class), key=lambda e: e.id())


def name(element):
    """The element's Name attribute, or None."""
    return getattr(element, "Name", None)


def pset_value(model, element, pset, prop):
    """Value of a property in a property set of the element, or None if the set or property is absent."""
    if element is None:
        return None
    return ifcopenshell.util.element.get_psets(element).get(pset, {}).get(prop)


def declared_quantity(model, element, qto, quantity):
    """A quantity declared in a Qto set (length in metres, area in m2, volume in m3, other kinds unchanged), or None."""
    if element is None:
        return None
    for rel in getattr(element, "IsDefinedBy", None) or []:
        definition = getattr(rel, "RelatingPropertyDefinition", None)
        if definition is None or not definition.is_a("IfcElementQuantity") or definition.Name != qto:
            continue
        for q in definition.Quantities:
            if q.Name != quantity:
                continue
            attribute, unit_type = _QUANTITIES.get(q.is_a(), (None, None))
            if attribute is None:
                return None
            scale = ifcopenshell.util.unit.calculate_unit_scale(model, unit_type)
            if unit_type == "LENGTHUNIT":
                scale = ifcopenshell.util.unit.calculate_unit_scale(model)
            value = getattr(q, attribute)
            return None if value is None else float(value) * scale
    return None


def building_occupancy(model, element):
    """Pset_BuildingCommon.OccupancyType of the IfcBuilding that contains/aggregates the element, or None."""
    current = element
    for _ in range(12):
        if current is None:
            return None
        if current.is_a("IfcBuilding"):
            value = pset_value(model, current, "Pset_BuildingCommon", "OccupancyType")
            return value if isinstance(value, str) and value else None
        current = ifcopenshell.util.element.get_container(current) or ifcopenshell.util.element.get_aggregate(current)
    return None


def _mesh(model, element, world: bool):
    """(vertices in metres, triangles) of the element's body geometry, or None if it has none."""
    if element is None or not hasattr(element, "Representation") or element.Representation is None:
        return None
    settings = ifcopenshell.geom.settings()
    settings.set("USE_WORLD_COORDS", world)
    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
    except Exception:  # no usable geometry: the value cannot be computed
        return None
    # ifcopenshell.geom already converts to SI: the vertices are in metres whatever the project length unit, so
    # they are not scaled again (doing so made millimetre models 1000x too small; tests/test_length_units.py).
    v, f = shape.geometry.verts, shape.geometry.faces
    if not v or not f:
        return None
    verts = [(v[i], v[i + 1], v[i + 2]) for i in range(0, len(v), 3)]
    return verts, [tuple(f[i:i + 3]) for i in range(0, len(f), 3)]


def space_floor_area_m2(model, space):
    """Floor area of a space in m2: the area of the downward-facing faces of its body geometry (the footprint of an
    extruded solid). None when the space has no geometry."""
    mesh = _mesh(model, space, world=True)
    if mesh is None:
        return None
    verts, triangles = mesh
    area = 0.0
    for a, b, c in triangles:
        p, q, r = verts[a], verts[b], verts[c]
        u = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
        w = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        length = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if length > 0 and n[2] / length < -0.999:
            area += length / 2
    return area if area > 0 else None


def element_height_m(model, element):
    """Vertical extent of the element's body geometry in metres (a room's floor-to-slab height), or None."""
    mesh = _mesh(model, element, world=True)
    if mesh is None:
        return None
    z = [p[2] for p in mesh[0]]
    return max(z) - min(z)


def stair_flight_width_m(model, flight):
    """Width of a stair flight in metres: its geometry's extent along the flight's local Y axis (the run is along
    local X), or None when it has no geometry."""
    mesh = _mesh(model, flight, world=False)
    if mesh is None:
        return None
    y = [p[1] for p in mesh[0]]
    return max(y) - min(y)


def finding(element, verdict, detail, measured=None, required=None):
    """One result: verdict 'pass' | 'fail' | 'unchecked' for the element, a plain sentence in `detail`, and the
    computed and required values (in m or m2) where there are any."""
    return {"global_id": element.GlobalId, "verdict": verdict, "detail": detail,
            "measured": measured, "required": required}


def validate_finding(value):
    """None if `value` is a well-formed finding dict, else a description of what is wrong."""
    if not isinstance(value, dict):
        return f"finding is a {type(value).__name__}, not a dict"
    if set(value) != FINDING_KEYS:
        return f"finding keys {sorted(value)} != {sorted(FINDING_KEYS)}"
    if not isinstance(value["global_id"], str) or not value["global_id"]:
        return "global_id must be a non-empty string"
    if value["verdict"] not in VERDICTS:
        return f"verdict must be one of {VERDICTS}"
    if not isinstance(value["detail"], str):
        return "detail must be a string"
    for key in ("measured", "required"):
        v = value[key]
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)):
            return f"{key} must be a finite number or None"
    return None


PUBLIC = (elements, name, pset_value, declared_quantity, building_occupancy, space_floor_area_m2, element_height_m,
          stair_flight_width_m, finding)
HELPERS = SimpleNamespace(**{fn.__name__: fn for fn in PUBLIC})


@dataclass(frozen=True)
class Signature:
    name: str
    signature: str
    doc: str


def signatures() -> list[Signature]:
    """The public helper API, read from the functions themselves so prompts cannot drift from the code."""
    return [Signature(fn.__name__, str(inspect.signature(fn)), inspect.getdoc(fn) or "") for fn in PUBLIC]
