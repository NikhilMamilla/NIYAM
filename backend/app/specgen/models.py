"""Rule specs (rules/specs/<unit>.yaml): one small hand-written file per rule unit, validated strictly.

A spec is input, never derived from running anything. The loader rejects a spec whose unit_text is not a verbatim
(whitespace-normalised) substring of its parent clause, or whose threshold number does not occur in that text."""

import re
from pathlib import Path
from typing import Literal

import ifcopenshell
import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from app.corpus.models import Clause
from app.fixtures.builders import REPO_ROOT, safe_name

SPECS_DIR = REPO_ROOT / "rules" / "specs"
CLAUSES_SNAPSHOT = SPECS_DIR / "clauses.yaml"  # parent clauses of every spec, so validation needs no database
TEMPLATES = ("door_width_min", "door_operation_forbidden", "space_area_min", "space_height_min")
TIER = {"door_width_min": "ids", "door_operation_forbidden": "ids", "space_area_min": "geometric",
        "space_height_min": "geometric"}
# selection data the modelling profile defines (docs/modelling-profile.md)
DOOR_SELECTORS = {("Pset_DoorCommon", "FireExit")}
DOOR_OPERATIONS = set(ifcopenshell.ifcopenshell_wrapper.schema_by_name("IFC4")
                      .declaration_by_name("IfcDoorTypeOperationEnum").enumeration_items())


class SpecError(ValueError):
    pass


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Selector(_Strict):
    pset: str
    property: str
    value: bool | str


class Threshold(_Strict):
    value: float
    text: str  # the number exactly as written in the clause, e.g. "2.75" or "1"
    unit: Literal["m", "m2"]
    inclusive: bool  # True: "not less than" (>=); False: "more than" (>)

    @model_validator(mode="after")
    def _text_is_the_value(self):
        if not re.fullmatch(r"\d+(\.\d+)?", self.text) or float(self.text) != self.value:
            raise ValueError(f"threshold text {self.text!r} must be the number {self.value} as written")
        if self.value <= 0:
            raise ValueError("threshold must be positive")
        return self


class Params(_Strict):
    selector: Selector | None = None  # door templates
    forbidden_operations: list[str] | None = None  # door_operation_forbidden
    categories: list[str] | None = None  # space templates: Pset_SpaceCommon.Category values in scope


class Spec(_Strict):
    unit_id: str
    clause_id: str
    unit_text: str
    topic: str
    template: Literal["door_width_min", "door_operation_forbidden", "space_area_min", "space_height_min"]
    params: Params
    threshold: Threshold | None = None
    notes_for_reviewer: str

    @property
    def tier(self) -> str:
        return TIER[self.template]

    @property
    def safe(self) -> str:
        return safe_name(self.unit_id)

    @model_validator(mode="after")
    def _template_fields(self):
        t, p = self.template, self.params
        if not self.unit_id.startswith(self.clause_id + "#"):
            raise ValueError(f"unit_id {self.unit_id} must be {self.clause_id}#<suffix>")
        if t.startswith("door"):
            if p.selector is None or (p.selector.pset, p.selector.property) not in DOOR_SELECTORS:
                raise ValueError(f"{t} needs a selector from the modelling profile: {sorted(DOOR_SELECTORS)}")
            if p.categories is not None:
                raise ValueError(f"{t} takes no categories")
        else:
            if not p.categories or p.selector is not None or p.forbidden_operations is not None:
                raise ValueError(f"{t} needs categories (Pset_SpaceCommon.Category values) and nothing else")
        if t == "door_operation_forbidden":
            bad = [o for o in p.forbidden_operations or [] if o not in DOOR_OPERATIONS]
            if not p.forbidden_operations or bad:
                raise ValueError(f"forbidden_operations must be IfcDoorTypeOperationEnum values; bad: {bad}")
            if self.threshold is not None:
                raise ValueError("door_operation_forbidden takes no threshold")
        else:
            if self.threshold is None:
                raise ValueError(f"{t} needs a threshold")
            want = "m2" if t == "space_area_min" else "m"
            if self.threshold.unit != want:
                raise ValueError(f"{t} threshold unit must be {want}, not {self.threshold.unit}")
            if p.forbidden_operations is not None:
                raise ValueError(f"{t} takes no forbidden_operations")
            if t == "door_width_min" and not self.threshold.inclusive:
                # IDS compares the unit-converted quantity: 900 mm reads 0.9000000000000001 m, so "> 0.9" would pass
                raise ValueError("door_width_min supports inclusive thresholds only (exclusive IDS bounds are unsafe "
                                 "on unit-converted values)")
        return self


def _squash(text: str) -> str:
    return " ".join(text.split())


def load_snapshot(path: Path = CLAUSES_SNAPSHOT) -> dict[str, Clause]:
    if not path.exists():
        return {}
    return {c["id"]: Clause(**c) for c in yaml.safe_load(path.read_text(encoding="utf-8")) or []}


def parent_clause(clause_id: str, db: Path | None = None) -> Clause:
    """The clause from the corpus database when it has it, else from the committed snapshot."""
    from app.corpus import repository as repo

    db = db or repo.DEFAULT_DB
    if db.exists():
        conn = repo.connect(db)
        try:
            repo.init_db(conn)
            clause = repo.get_clause(conn, clause_id)
        finally:
            conn.close()
        if clause is not None:
            return clause
    snapshot = load_snapshot()
    if clause_id not in snapshot:
        raise SpecError(f"clause {clause_id} is neither in the corpus database nor in {CLAUSES_SNAPSHOT.name}")
    return snapshot[clause_id]


def check_against_clause(spec: Spec, clause: Clause) -> None:
    if _squash(spec.unit_text) not in _squash(clause.text):
        raise SpecError(f"{spec.unit_id}: unit_text is not a verbatim substring of {clause.id}")
    if spec.threshold is not None:
        number = re.compile(rf"(?<![\d.]){re.escape(spec.threshold.text)}(?![\d]|\.\d)")
        if not (number.search(spec.unit_text) or number.search(clause.text)):
            raise SpecError(f"{spec.unit_id}: threshold {spec.threshold.text!r} does not occur in the unit or clause text")


def load_spec(path: Path, db: Path | None = None) -> Spec:
    try:
        spec = Spec(**(yaml.safe_load(path.read_text(encoding="utf-8")) or {}))
    except (ValueError, yaml.YAMLError) as e:  # pydantic.ValidationError is a ValueError
        raise SpecError(f"{path.name}: {e}") from e
    if path.stem != spec.safe:
        raise SpecError(f"{path.name}: file name must be {spec.safe}.yaml")
    check_against_clause(spec, parent_clause(spec.clause_id, db))
    return spec


def spec_paths(root: Path = SPECS_DIR) -> list[Path]:
    return sorted(p for p in root.glob("*.yaml") if p.name != CLAUSES_SNAPSHOT.name)


def load_all(root: Path = SPECS_DIR, db: Path | None = None) -> list[Spec]:
    return [load_spec(p, db) for p in spec_paths(root)]
