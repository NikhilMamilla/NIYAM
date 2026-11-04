from typing import Literal

from pydantic import BaseModel

Verdict = Literal["passed", "failed", "unchecked", "out_of_scope"]
Status = Literal["compliant", "noncompliant", "incomplete", "nothing_checked"]


class Counts(BaseModel):
    passed: int = 0
    failed: int = 0
    unchecked: int = 0
    out_of_scope: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(**{k: getattr(self, k) + getattr(other, k) for k in Counts.model_fields})


class ElementResult(BaseModel):
    global_id: str
    name: str | None
    ifc_class: str
    verdict: Verdict
    reason: str | None = None


class RuleResult(BaseModel):
    unit_id: str
    clause_id: str
    clause_text: str
    rule_text: str
    source_doc: str
    page: int
    severity: str
    human_reviewed: bool
    status: Status
    counts: Counts
    elements: list[ElementResult]


class AuditReport(BaseModel):
    ifc_file: str
    ifc_schema: str
    rulepack_version: str
    status: Status
    summary: Counts
    rules: list[RuleResult]
