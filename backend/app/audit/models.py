from typing import Literal

from pydantic import BaseModel

Verdict = Literal["passed", "failed", "unchecked", "out_of_scope"]
Status = Literal["compliant", "noncompliant", "incomplete", "nothing_checked"]
RuleStatus = Literal["compliant", "noncompliant", "incomplete", "nothing_checked", "error"]


class Counts(BaseModel):
    passed: int = 0
    failed: int = 0
    unchecked: int = 0
    out_of_scope: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(**{k: getattr(self, k) + getattr(other, k) for k in Counts.model_fields})


class ElementCounts(BaseModel):
    """Distinct elements, each counted once: any failed rule -> with_failed, else any unchecked -> with_unchecked."""

    total_in_model_of_scoped_classes: int = 0
    with_failed: int = 0
    with_unchecked: int = 0
    clean: int = 0


class Summary(BaseModel):
    checks: Counts  # rule x element checks: one element is counted once per rule
    elements: ElementCounts
    rules_with_errors: int = 0  # geometric rules whose check timed out or crashed: not checked, not passed


class ElementResult(BaseModel):
    global_id: str
    express_id: int  # STEP id in the audited file; lets a viewer map results to geometry
    name: str | None
    ifc_class: str
    verdict: Verdict
    reason_plain: str | None = None  # one plain-English sentence, from rule scope and element data
    reason_raw: str | None = None  # the underlying ifctester or engine message


class RuleResult(BaseModel):
    unit_id: str
    clause_id: str
    clause_text: str
    rule_text: str
    source_doc: str
    page: int
    severity: str
    human_reviewed: bool
    status: RuleStatus
    counts: Counts
    elements: list[ElementResult]
    error: str | None = None  # why a rule has status "error"


class AuditReport(BaseModel):
    ifc_file: str
    ifc_schema: str
    rulepack_version: str
    status: Status
    summary: Summary
    rules: list[RuleResult]

    def element_noun(self) -> str:
        classes = {e.ifc_class for r in self.rules for e in r.elements}
        return "doors" if classes == {"IfcDoor"} else "elements"

    def checks_line(self) -> str:
        c = self.summary.checks
        return (f"Checks run: passed {c.passed}, failed {c.failed}, unchecked {c.unchecked}, "
                f"out of scope {c.out_of_scope}")

    def elements_line(self) -> str:
        e = self.summary.elements
        return (f"{self.element_noun().capitalize()} affected: {e.with_failed} with violations, "
                f"{e.with_unchecked} could not be fully checked (of {e.total_in_model_of_scoped_classes} in scope classes)")
