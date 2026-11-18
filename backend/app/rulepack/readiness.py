"""One buildingSMART IDS 1.0 file listing the data a model must carry for NIYAM's rules to be checkable.

Derived from the rules, not from a list: the rule specs (rules/specs/*.yaml) and the hand-written rules of rulepack v0
(their manifest scope, and the Category each room check compares against). Each requirement's instructions name the
units it enables. It checks that data is present, never whether a building complies."""

import re
from collections import defaultdict

from ifctester import ids

from app.fixtures.builders import REPO_ROOT
from app.rulepack.loader import DEFAULT_PACK, load_rulepack
from app.specgen.models import load_all

DEFAULT_OUT = REPO_ROOT / "docs" / "readiness" / "niyam-data-readiness.ids"
PROFILE_NOTE = ("Category names are NIYAM's assumed profile (docs/modelling-profile.md), not a standard; "
                "they have not been seen in real authoring-tool exports.")


def needs(pack=DEFAULT_PACK) -> dict[str, set[str]]:
    """{data item: unit ids that need it}. Data items: 'Category:<value>', 'FireExit', 'Width', 'Height',
    'OperationType', 'OccupancyType'."""
    out: dict[str, set[str]] = defaultdict(set)
    for spec in load_all():
        if spec.template in ("space_area_min", "space_height_min"):
            for category in spec.params.categories:
                out[f"Category:{category}"].add(spec.unit_id)
        else:
            out["FireExit"].add(spec.unit_id)
            out[{"door_width_min": "Width", "door_height_min": "Height"}.get(spec.template, "OperationType")].add(
                spec.unit_id)
    rulepack = load_rulepack(pack)
    for rule in rulepack.manifest.rules:
        for item in rule.scope.required_data:
            key = item.attribute or item.name
            if key == "Category":  # the value comes from the check itself: `category != "Habitable"`
                source = (pack / rule.check_file).read_text(encoding="utf-8")
                for category in re.findall(r'category != "([A-Za-z]+)"', source):
                    out[f"Category:{category}"].add(rule.unit_id)
            else:
                out[key].add(rule.unit_id)
    return dict(out)


def _units(ids_: set[str]) -> str:
    return ", ".join(sorted(ids_))


def build_ids(pack=DEFAULT_PACK) -> str:
    data = needs(pack)
    categories = sorted(k.split(":", 1)[1] for k in data if k.startswith("Category:"))
    space_units = set().union(*(data[f"Category:{c}"] for c in categories))
    doc = ids.Ids(title="NIYAM data readiness", version="0.1",
                  description="What a model must carry before NIYAM can check its rules. Presence only, not "
                              "compliance. Generated from the rule specs and rulepack v0.")

    def spec(name, applicability, requirement, instructions):
        s = ids.Specification(name=name, ifcVersion=["IFC4"], instructions=instructions)
        s.applicability += applicability
        s.requirements.append(requirement)
        doc.specifications.append(s)

    exit_door = [ids.Entity(name="IFCDOOR"),
                 ids.Property(propertySet="Pset_DoorCommon", baseName="FireExit", value="TRUE", dataType="IFCBOOLEAN")]
    spec("Spaces declare a profile Category", [ids.Entity(name="IFCSPACE")],
         ids.Property(propertySet="Pset_SpaceCommon", baseName="Category", dataType="IFCLABEL",
                      value=ids.Restriction(options={"enumeration": categories})),
         f"Enables {_units(space_units)}. Room rules also need Body geometry (not expressible in IDS). {PROFILE_NOTE}")
    spec("Doors declare Pset_DoorCommon.FireExit", [ids.Entity(name="IFCDOOR")],
         ids.Property(propertySet="Pset_DoorCommon", baseName="FireExit", dataType="IFCBOOLEAN"),
         f"Enables {_units(data['FireExit'])}: door rules apply to exit doors (FireExit = TRUE).")
    spec("Exit doors carry Qto_DoorBaseQuantities.Width", exit_door,
         ids.Property(propertySet="Qto_DoorBaseQuantities", baseName="Width", dataType="IFCLENGTHMEASURE"),
         f"Enables {_units(data['Width'])}.")
    spec("Exit doors carry Qto_DoorBaseQuantities.Height", exit_door,
         ids.Property(propertySet="Qto_DoorBaseQuantities", baseName="Height", dataType="IFCLENGTHMEASURE"),
         f"Enables {_units(data['Height'])}.")
    spec("Exit doors declare OperationType", exit_door, ids.Attribute(name="OperationType"),
         f"Enables {_units(data['OperationType'])}.")
    spec("Buildings declare Pset_BuildingCommon.OccupancyType", [ids.Entity(name="IFCBUILDING")],
         ids.Property(propertySet="Pset_BuildingCommon", baseName="OccupancyType", dataType="IFCLABEL"),
         f"Enables {_units(data['OccupancyType'])}. The stair rule also needs IfcStairFlight Body geometry (its width "
         "is computed; not expressible in IDS).")
    return doc.to_string()
