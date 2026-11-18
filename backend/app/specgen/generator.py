"""Build everything a spec implies, deterministically: rule unit, dev pair, held-out pair with arithmetic truth,
gold artifact and dry-run answers. Element values come from the spec's threshold; expected verdicts are computed
from those values and the threshold, never by running a rule."""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from ifctester import ids

from app.corpus import repository as repo
from app.corpus.models import RuleUnit
from app.fixtures import geo_builders as gb
from app.fixtures.builders import FIXTURES_DIR, REPO_ROOT, FixturePair, _stabilise, add_door, guid, new_model
from app.fixtures.gold_ids import GOLD_DIR, UNITS_YAML, check_duplicates
from app.fixtures.heldout import HELDOUT_DIR
from app.specgen.models import CLAUSES_SNAPSHOT, SPECS_DIR, Spec, load_all, parent_clause, spec_paths

CHECKS_DIR = REPO_ROOT / "fixtures" / "checks"
DRYRUN_DIR = REPO_ROOT / "backend" / "app" / "eval" / "dryrun"
ALLOWED_OPS = ["SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "DOUBLE_DOOR_DOUBLE_SWING", "DOUBLE_DOOR_SINGLE_SWING"]
CONTROL_CATEGORY = "Corridor"
MEASURE = {"space_area_min": ("space_floor_area_m2", "floor area", "m2"),
           "space_height_min": ("element_height_m", "room height", "m")}


def units_of(spec: Spec) -> tuple[str, str]:
    """(dev, held-out) project length units: alternate by the spec's position so both are exercised."""
    if spec.dev_length_unit is not None:  # pinned, so adding specs never shifts other units' fixtures
        return (spec.dev_length_unit, "m" if spec.dev_length_unit == "mm" else "mm")
    unpinned = [p.stem for p in spec_paths() if "dev_length_unit" not in p.read_text(encoding="utf-8")]
    return ("mm", "m") if unpinned.index(spec.safe) % 2 == 0 else ("m", "mm")


def meets(spec: Spec, value: float) -> bool:
    t = spec.threshold
    return value >= t.value if t.inclusive else value > t.value


# --- element plans: (name, in scope?, value) -> expected verdict computed arithmetically -------------------------


@dataclass(frozen=True)
class Element:
    name: str
    selected: bool  # FireExit TRUE / category in scope
    value: float | str  # width, area or height in m / m2, or a door operation


def _r(x: float) -> float:
    return round(x, 4)


def dev_elements(spec: Spec) -> dict[str, list[Element]]:
    tag, t = spec.safe, spec.threshold
    if spec.template == "door_operation_forbidden":
        allowed = next(o for o in ALLOWED_OPS if o not in spec.params.forbidden_operations)
        bad = spec.params.forbidden_operations[0]
        return {k: [Element(f"{tag} under test", True, v), Element(f"{tag} control", False, bad)]
                for k, v in (("pass", allowed), ("fail", bad))}
    if t.inclusive:
        good, bad = t.value, _r(t.value * 0.9)  # exactly the bound passes
    else:
        good, bad = _r(t.value * 1.1), t.value  # exactly the bound fails
    control = _r(t.value * 0.5)
    return {k: [Element(f"{tag} under test", True, v), Element(f"{tag} control", False, control)]
            for k, v in (("pass", good), ("fail", bad))}


def heldout_elements(spec: Spec) -> dict[str, list[Element]]:
    tag, t = spec.safe, spec.threshold
    if spec.template == "door_operation_forbidden":
        allowed = [o for o in ALLOWED_OPS if o not in spec.params.forbidden_operations]
        forbidden = spec.params.forbidden_operations
        return {
            "pass": [Element(f"HO {tag} exit {allowed[1].lower()}", True, allowed[1]),
                     Element(f"HO {tag} exit {allowed[2].lower()}", True, allowed[2]),
                     Element(f"HO {tag} non-exit {forbidden[-1].lower()}", False, forbidden[-1])],
            "fail": [*(Element(f"HO {tag} exit {op.lower()}", True, op) for op in forbidden[-3:]),
                     Element(f"HO {tag} exit {allowed[0].lower()}", True, allowed[0])],
        }
    v = t.value
    edge_pass, edge_fail = (v, _r(v - 0.01)) if t.inclusive else (_r(v + 0.01), v)
    return {
        "pass": [Element(f"HO {tag} at the bound {edge_pass:g}", True, edge_pass),
                 Element(f"HO {tag} ample {_r(v * 1.3):g}", True, _r(v * 1.3)),
                 Element(f"HO {tag} out of scope {_r(v * 0.6):g}", False, _r(v * 0.6))],
        "fail": [Element(f"HO {tag} just failing {edge_fail:g}", True, edge_fail),
                 Element(f"HO {tag} comfortable {_r(v * 1.2):g}", True, _r(v * 1.2)),
                 Element(f"HO {tag} out of scope {_r(v * 0.4):g}", False, _r(v * 0.4))],
    }


def expected(spec: Spec, e: Element) -> str:
    if not e.selected:
        return "out_of_scope"
    if spec.template == "door_operation_forbidden":
        return "fail" if e.value in spec.params.forbidden_operations else "pass"
    return "pass" if meets(spec, e.value) else "fail"


# --- IFC models ---------------------------------------------------------------------------------------------------


def _model(spec: Spec, elements: list[Element], length_unit: str, key: str):
    f, storey = new_model(f"NIYAM generated {spec.unit_id} {key}", length_unit=length_unit)
    scale = 1000.0 if length_unit == "mm" else 1.0
    x = 0.0
    for e in elements:
        if spec.template.startswith("door"):
            width = e.value if spec.template == "door_width_min" else 1.2
            height = e.value if spec.template == "door_height_min" else 2.1
            op = e.value if spec.template == "door_operation_forbidden" else "SINGLE_SWING_LEFT"
            add_door(f, storey, e.name, fire_exit=e.selected, operation_type=op, width=width * scale,
                     height=height * scale)
            continue
        category = spec.params.categories[0] if e.selected else CONTROL_CATEGORY
        if spec.template == "space_area_min":
            depth = 1.0 if e.value <= 4 else 2.5
            gb.add_space(f, storey, e.name, category=category, size_x_m=e.value / depth, size_y_m=depth,
                         height_m=2.75, x_m=x)
            x += e.value / depth + 0.5
        else:
            gb.add_space(f, storey, e.name, category=category, size_x_m=3.0, size_y_m=3.0, height_m=e.value, x_m=x)
            x += 3.5
    _stabilise(f, key, keep_names=frozenset(e.name for e in elements))
    return f


def dev_pair(spec: Spec, root: Path = FIXTURES_DIR) -> FixturePair:
    return FixturePair(root / f"{spec.safe}__pass.ifc", root / f"{spec.safe}__fail.ifc",
                       frozenset({guid(f"{spec.safe} under test")}))


def heldout_paths(spec: Spec, root: Path = HELDOUT_DIR) -> dict[str, Path]:
    return {"pass": root / f"{spec.safe}__heldout_pass.ifc", "fail": root / f"{spec.safe}__heldout_fail.ifc",
            "truth": root / f"{spec.safe}.truth.json"}


# --- gold artifacts -----------------------------------------------------------------------------------------------


def gold_ids(spec: Spec, threshold: float | None = None, forbidden: list[str] | None = None,
             cardinality: str = "prohibited") -> str:
    doc = ids.Ids(title=f"NIYAM generated IDS {spec.unit_id}",
                  description="DRAFT generated from a rule spec; human_reviewed=false.", version="0.1")
    spec_ids = ids.Specification(name=f"{spec.unit_id} {spec.topic}", ifcVersion=["IFC4"], identifier=spec.unit_id,
                                 description=" ".join(spec.unit_text.split()),
                                 instructions=f"Source: MBBL-2016 clause {spec.clause_id}. Draft, not human-reviewed.")
    sel = spec.params.selector
    spec_ids.applicability.append(ids.Entity(name="IFCDOOR"))
    value = ("TRUE" if sel.value else "FALSE") if isinstance(sel.value, bool) else sel.value
    spec_ids.applicability.append(ids.Property(propertySet=sel.pset, baseName=sel.property, value=value,
                                               dataType="IFCBOOLEAN" if isinstance(sel.value, bool) else "IFCLABEL"))
    if spec.template in ("door_width_min", "door_height_min"):
        bound = spec.threshold.value if threshold is None else threshold
        spec_ids.requirements.append(ids.Property(
            propertySet="Qto_DoorBaseQuantities", baseName="Width" if spec.template == "door_width_min" else "Height",
            dataType="IFCLENGTHMEASURE",
            value=ids.Restriction(options={"minInclusive": bound}, base="double")))
    else:
        ops = forbidden or spec.params.forbidden_operations
        value = ops[0] if len(ops) == 1 else ids.Restriction(options={"enumeration": ops})
        spec_ids.requirements.append(ids.Attribute(name="OperationType", value=value, cardinality=cardinality))
    doc.specifications.append(spec_ids)
    return doc.to_string()


CHECK_TEMPLATE = '''import math


def check(model, helpers):
    """{unit_id}: {label} of {rooms} {word} {text} {unit}. DRAFT generated from a rule spec, not human-reviewed."""
    required = {required}
    categories = {categories}
    findings = []
    for space in helpers.elements(model, "IfcSpace"):
        category = helpers.pset_value(model, space, "Pset_SpaceCommon", "Category")
        if category is None:
            findings.append(helpers.finding(
                space, "unchecked",
                "This space does not declare its category (Pset_SpaceCommon.Category), so it is unknown "
                "whether the rule applies."))
            continue
        if category not in categories:
            continue
        value = helpers.{measure}(model, space)
        if value is None:
            findings.append(helpers.finding(
                space, "unchecked", "This space has no geometry, so its {label} could not be computed."))
            continue
        verdict = "pass" if {comparison} else "fail"
        findings.append(helpers.finding(
            space, verdict,
            f"Computed {label} is {{value:.2f}} {unit}; this rule requires {word} {{required:g}} {unit}.",
            measured=value, required=required))
    return findings
'''


def gold_check(spec: Spec, threshold: float | None = None, inclusive: bool | None = None,
               invert: bool = False) -> str:
    measure, label, unit = MEASURE[spec.template]
    inclusive = spec.threshold.inclusive if inclusive is None else inclusive
    comparison = "value >= required - 1e-9" if inclusive else "value > required + 1e-9"
    if invert:
        comparison = "value <= required + 1e-9"
    return CHECK_TEMPLATE.format(
        unit_id=spec.unit_id, label=label, rooms=" / ".join(spec.params.categories), word="at least" if inclusive
        else "more than", text=spec.threshold.text, unit=unit, measure=measure, comparison=comparison,
        required=repr(spec.threshold.value if threshold is None else threshold),
        categories=repr(tuple(spec.params.categories)))


def gold_artifact(spec: Spec) -> tuple[Path, str]:
    if spec.tier == "ids":
        return GOLD_DIR / f"{spec.safe}.ids", gold_ids(spec)
    return CHECKS_DIR / f"{spec.safe}.py", gold_check(spec)


def overfit(spec: Spec) -> str:
    """A rule tuned to the dev pair instead of the clause: it passes the dev gate and fails held-out."""
    t = spec.threshold
    if spec.template in ("door_width_min", "door_height_min"):
        return gold_ids(spec, threshold=_r(t.value - 0.05))  # between the dev fail (-10%) and pass values
    if spec.template == "door_operation_forbidden":
        return gold_ids(spec, forbidden=spec.params.forbidden_operations[:1])  # only the operation dev shows
    return gold_check(spec, threshold=_r(t.value * 0.95))


def dryrun_answers(spec: Spec) -> dict[str, str]:
    """Synthetic answers for the DryRunProvider (test data only, never shown to a real model)."""
    if spec.tier == "ids":
        answers = {"correct.ids": gold_ids(spec), "inverted.ids": gold_ids(spec, cardinality="required")
                   if spec.template == "door_operation_forbidden" else gold_ids(spec, threshold=spec.threshold.value * 2),
                   "malformed.ids": gold_ids(spec)[:400]}
        if spec.template != "door_operation_forbidden" or len(spec.params.forbidden_operations) > 1:
            answers["overfit.ids"] = overfit(spec)
        return answers
    return {"correct.py": gold_check(spec), "overfit.py": overfit(spec),
            "off_by_one.py": gold_check(spec, inclusive=not spec.threshold.inclusive),
            "inverted.py": gold_check(spec, invert=True), "malformed.py": gold_check(spec).replace("import math", "import os")}


# --- build --------------------------------------------------------------------------------------------------------


def rule_unit(spec: Spec, artifact: Path) -> RuleUnit:
    return RuleUnit(id=spec.unit_id, clause_id=spec.clause_id, text=spec.unit_text, tier=spec.tier, status="pilot",
                    expected_artifact=artifact.relative_to(REPO_ROOT).as_posix(), human_reviewed=False,
                    notes=" ".join(spec.notes_for_reviewer.split()), duplicate_of=spec.duplicate_of)


def build_files(spec: Spec, *, fixtures_dir=FIXTURES_DIR, heldout_dir=HELDOUT_DIR, artifact_dir: Path | None = None,
                dryrun_dir=DRYRUN_DIR) -> dict[str, Path]:
    """Write the fixtures, truth, gold artifact and dry-run answers for one spec. Deterministic."""
    dev_unit, held_unit = units_of(spec)
    out = {}
    pair = dev_pair(spec, fixtures_dir)
    for kind, elements in dev_elements(spec).items():
        path = pair.pass_path if kind == "pass" else pair.fail_path
        _model(spec, elements, dev_unit, f"specgen/{spec.unit_id}/dev/{kind}").write(str(path))
        out[f"dev_{kind}"] = path
    held = heldout_paths(spec, heldout_dir)
    truth = {"unit_id": spec.unit_id, "length_unit": held_unit, "synthetic": True, "generated_from": f"rules/specs/{spec.safe}.yaml",
             "models": {}}
    for kind, elements in heldout_elements(spec).items():
        _model(spec, elements, held_unit, f"specgen/{spec.unit_id}/heldout/{kind}").write(str(held[kind]))
        truth["models"][held[kind].name] = [{"name": e.name, "global_id": guid(e.name), "expected": expected(spec, e)}
                                            for e in elements]
        out[f"heldout_{kind}"] = held[kind]
    held["truth"].write_text(json.dumps(truth, indent=2) + "\n", encoding="utf-8")
    out["truth"] = held["truth"]
    path, text = gold_artifact(spec)
    if artifact_dir is not None:
        path = artifact_dir / path.name
    path.write_text(text, encoding="utf-8")
    out["gold"] = path
    answers = dryrun_dir / spec.safe
    answers.mkdir(parents=True, exist_ok=True)
    for name, text in dryrun_answers(spec).items():
        (answers / name).write_text(text, encoding="utf-8")
    return out


def register_units(specs: list[Spec], units_yaml: Path = UNITS_YAML, db: Path | None = None,
                   snapshot: Path = CLAUSES_SNAPSHOT) -> None:
    """Add the specs' rule units to rule-units.yaml (and the corpus DB if present); snapshot their parent clauses."""
    units = {u["id"]: RuleUnit(**u) for u in yaml.safe_load(units_yaml.read_text(encoding="utf-8")) or []}
    for spec in specs:
        units[spec.unit_id] = rule_unit(spec, gold_artifact(spec)[0])
    check_duplicates(units.values())  # targets must exist, differ, and not be duplicates themselves
    with open(units_yaml, "w", encoding="utf-8") as fh:  # same layout as repository.export_units (sorted by id)
        yaml.safe_dump([units[k].model_dump() for k in sorted(units)], fh, allow_unicode=True, sort_keys=False,
                       width=100)
    clauses = {s.clause_id: parent_clause(s.clause_id, db) for s in specs}
    with open(snapshot, "w", encoding="utf-8") as fh:
        yaml.safe_dump([clauses[k].model_dump() for k in sorted(clauses)], fh, allow_unicode=True, sort_keys=False,
                       width=100)
    db = db or repo.DEFAULT_DB
    if db.exists():
        conn = repo.connect(db)
        repo.init_db(conn)
        for spec in specs:
            repo.upsert_unit(conn, units[spec.unit_id])
        conn.close()


def build_all(root: Path = SPECS_DIR) -> list[Spec]:
    specs = load_all(root)
    for spec in specs:
        build_files(spec)
    register_units(specs)
    return specs
