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
