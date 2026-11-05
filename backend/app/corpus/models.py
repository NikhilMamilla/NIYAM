from typing import Literal

from pydantic import BaseModel

Tier = Literal["ids", "geometric", "out_of_scope", "unclassified"]
Status = Literal["candidate", "selected", "rejected"]


class Clause(BaseModel):
    id: str
    source_doc: str
    clause_number: str
    title: str | None = None
    text: str
    page: int
    section_path: list[str] = []
    tier: Tier = "unclassified"
    topic: str | None = None
    status: Status = "candidate"
    notes: str | None = None


class RuleUnit(BaseModel):
    id: str
    clause_id: str
    text: str
    tier: Tier = "unclassified"
    status: Literal["pilot", "selected", "needs_rework", "rejected"] = "pilot"
    expected_artifact: str | None = None
    human_reviewed: bool = False
    reviewer: str | None = None
    notes: str | None = None
    reviewed_on: str | None = None  # ISO date of the reviewer's decision
    duplicate_of: str | None = None  # another unit that encodes the same requirement (a reviewer may reject the claim)
