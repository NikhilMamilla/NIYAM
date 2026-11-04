from dataclasses import dataclass
from pathlib import Path

import ifcopenshell
import pydantic
import yaml
from ifctester import ids

from app.fixtures.builders import REPO_ROOT
from app.rulepack.models import Manifest, RequiredData, Rule, Scope, Selector
from app.verifier.ids_gate import static_check

RULEPACK_DIR = REPO_ROOT / "rules" / "rulepack"
DEFAULT_PACK = RULEPACK_DIR / "v0"
_IFC4 = ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC4")


class RulepackError(Exception):
    pass


@dataclass
class Rulepack:
    root: Path
    manifest: Manifest

    def ids_xml(self, rule: Rule) -> str:
        return (self.root / rule.ids_file).read_text(encoding="utf-8")


def read_manifest(root: Path) -> Manifest | None:
    path = root / "manifest.yaml"
    if not path.exists():
        return None
    try:
        return Manifest(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
    except pydantic.ValidationError as e:
        raise RulepackError(f"{path}: invalid manifest:\n{e}") from e


def write_manifest(root: Path, manifest: Manifest) -> None:
    root.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(manifest.model_dump(exclude_none=True), allow_unicode=True, sort_keys=False, width=100)
    (root / "manifest.yaml").write_text(text, encoding="utf-8")


def load_rulepack(root: Path = DEFAULT_PACK) -> Rulepack:
    manifest = read_manifest(root)
    if manifest is None:
        raise RulepackError(f"no manifest.yaml in {root}")
    for rule in manifest.rules:
        path = root / rule.ids_file
        if not path.is_file():
            raise RulepackError(f"{rule.unit_id}: ids_file {rule.ids_file} is missing")
        result = static_check(path.read_text(encoding="utf-8"))
        if not result.accepted:
            f = result.first_failure
            raise RulepackError(f"{rule.unit_id}: {rule.ids_file} fails {f.stage}: {f.message}")
    return Rulepack(root, manifest)


def _simple(value, what: str) -> str:
    if not isinstance(value, str):
        raise RulepackError(f"cannot derive a scope from a restricted {what}; use a simple value")
    return value


def _data_item(facet) -> RequiredData:
    if isinstance(facet, ids.Attribute):
        return RequiredData(attribute=_simple(facet.name, "attribute name"))
    pset, name = _simple(facet.propertySet, "property set"), _simple(facet.baseName, "property name")
    return RequiredData(qto=pset, name=name) if pset.startswith("Qto_") else RequiredData(pset=pset, name=name)


def scope_from_ids(xml: str) -> Scope:
    """Read the scope a rule's single IDS specification checks: its class, selector and required data."""
    specs = ids.from_string(xml).specifications
    if len(specs) != 1:
        raise RulepackError(f"expected exactly one specification, found {len(specs)}")
    spec = specs[0]
    entities = [f for f in spec.applicability if isinstance(f, ids.Entity)]
    if len(entities) != 1:
        raise RulepackError("the applicability must contain exactly one entity facet")
    ifc_class = _IFC4.declaration_by_name(_simple(entities[0].name, "entity")).name()

    selector, items = None, []
    for facet in spec.applicability + spec.requirements:
        if isinstance(facet, ids.Entity):
            continue
        if not isinstance(facet, (ids.Attribute, ids.Property)):
            raise RulepackError(f"{type(facet).__name__} facets are not supported in rule scopes yet")
        item = _data_item(facet)
        if selector is None and facet in spec.applicability and isinstance(facet, ids.Property) and item.pset \
                and isinstance(facet.value, str):
            value = {"TRUE": True, "FALSE": False}.get(facet.value.upper(), facet.value) \
                if (facet.dataType or "").upper() == "IFCBOOLEAN" else facet.value
            selector = Selector(pset=item.pset, property=item.name, value=value)
        if item.key not in [i.key for i in items]:
            items.append(item)
    return Scope(ifc_class=ifc_class, selector=selector, required_data=items)
