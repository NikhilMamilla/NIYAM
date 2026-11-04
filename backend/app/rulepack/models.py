from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Selector(_Strict):
    pset: str
    property: str
    value: bool | int | float | str


class RequiredData(_Strict):
    """One data item a selected element must carry to be checkable: {pset, name}, {qto, name} or {attribute}."""

    pset: str | None = None
    qto: str | None = None
    attribute: str | None = None
    name: str | None = None

    @model_validator(mode="after")
    def _one_kind(self):
        kinds = [k for k in ("pset", "qto", "attribute") if getattr(self, k)]
        if len(kinds) != 1:
            raise ValueError(f"required_data needs exactly one of pset, qto, attribute; got {kinds or 'none'}")
        if (kinds[0] == "attribute") == (self.name is not None):
            raise ValueError("name is required for pset/qto items and not allowed for attribute items")
        return self

    @property
    def key(self) -> str:
        if self.attribute:
            return f"attribute:{self.attribute}"
        return f"pset:{self.pset}.{self.name}" if self.pset else f"qto:{self.qto}.{self.name}"


class Scope(_Strict):
    ifc_class: str
    selector: Selector | None = None
    required_data: list[RequiredData]
    measures: list[str] | None = None  # geometric rules: the helper-derived values the check computes


class Rule(_Strict):
    unit_id: str
    clause_id: str
    clause_text: str
    rule_text: str
    ids_file: str | None = None  # tier "ids"
    check_file: str | None = None  # tier "geometric": a Python check run only through the sandbox
    scope: Scope
    tier: Literal["ids", "geometric"] = "ids"
    source_doc: str
    page: int
    human_reviewed: bool = False
    severity: Literal["error", "warning"] = "error"

    @model_validator(mode="after")
    def _artifact_matches_tier(self):
        wanted, other = ("ids_file", "check_file") if self.tier == "ids" else ("check_file", "ids_file")
        if getattr(self, wanted) is None or getattr(self, other) is not None:
            raise ValueError(f"{self.unit_id}: a {self.tier} rule needs {wanted} and no {other}")
        return self


class Manifest(_Strict):
    version: str
    rules: list[Rule]

    @model_validator(mode="after")
    def _unique_units(self):
        seen = set()
        for rule in self.rules:
            if rule.unit_id in seen:
                raise ValueError(f"duplicate unit_id {rule.unit_id}")
            seen.add(rule.unit_id)
        return self
