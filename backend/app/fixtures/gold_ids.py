"""Draft gold IDS specs for the pilot rule units. Not human-reviewed."""

from pathlib import Path

import yaml
from ifctester import ids

from app.corpus.models import RuleUnit
from app.fixtures.builders import REPO_ROOT, safe_name

GOLD_DIR = REPO_ROOT / "fixtures" / "ids"
UNITS_YAML = REPO_ROOT / "rules" / "corpus" / "rule-units.yaml"
FIRE_EXIT_SLIDING_OR_OVERHEAD = ["SLIDING_TO_LEFT", "SLIDING_TO_RIGHT", "DOUBLE_DOOR_SLIDING", "ROLLINGUP"]


def load_units(path: Path = UNITS_YAML) -> dict[str, RuleUnit]:
    with open(path, encoding="utf-8") as fh:
        return {u["id"]: RuleUnit(**u) for u in yaml.safe_load(fh)}


def _requirement(unit_id: str):
    if unit_id == "MBBL2016-5.4.2#1":
        return ids.Attribute(name="OperationType", value="REVOLVING", cardinality="prohibited")
    if unit_id == "MBBL2016-5.4.1#b":
        # A quantity, not OverallWidth: ifctester converts quantities to SI but compares attributes raw.
        return ids.Property(
            propertySet="Qto_DoorBaseQuantities", baseName="Width", dataType="IFCLENGTHMEASURE",
            value=ids.Restriction(options={"minInclusive": 1.0}, base="double"),
        )
    if unit_id == "MBBL2016-5.4.1#c":
        return ids.Attribute(
            name="OperationType", cardinality="prohibited",
            value=ids.Restriction(options={"enumeration": FIRE_EXIT_SLIDING_OR_OVERHEAD}),
        )
    raise KeyError(f"no gold IDS defined for {unit_id}")


def build_gold(unit: RuleUnit) -> ids.Ids:
    doc = ids.Ids(
        title=f"NIYAM gold IDS {unit.id}",
        description="DRAFT gold IDS for a pilot rule unit; human_reviewed=false.",
        version="0.1",
    )
    spec = ids.Specification(
        name=f"{unit.id} fire-exit doors",
        ifcVersion=["IFC4"],
        identifier=unit.id,
        description=" ".join(unit.text.split()),
        instructions=f"Source: MBBL-2016 clause {unit.clause_id}. Draft encoding, not human-reviewed.",
    )
    spec.applicability.append(ids.Entity(name="IFCDOOR"))
    spec.applicability.append(
        ids.Property(propertySet="Pset_DoorCommon", baseName="FireExit", value="TRUE", dataType="IFCBOOLEAN")
    )
    spec.requirements.append(_requirement(unit.id))
    doc.specifications.append(spec)
    return doc


def build_all_gold(out_dir: Path = GOLD_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for unit in load_units().values():
        path = out_dir / f"{safe_name(unit.id)}.ids"
        if not build_gold(unit).to_xml(str(path)):
            raise ValueError(f"{path.name} is not valid against the IDS XSD")
        paths.append(path)
    return paths
