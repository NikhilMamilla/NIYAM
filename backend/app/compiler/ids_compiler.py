"""Compile one rule unit into an IDS 1.0 document with an LLM.

Gated mode: every candidate goes through the verifier gate; a rejection is fed back as a repair
turn until it is accepted or max_repairs rounds are used. Baseline mode (ablation): one call, no
repair; the gate only scores the candidate. The model never sees fixtures or gold IDS."""

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from app.corpus.models import Clause, RuleUnit
from app.fixtures.builders import REPO_ROOT, FixturePair, fixture_pair, safe_name
from app.llm.base import LLMProvider, Message
from app.verifier.ids_gate import GateResult, StageResult, verify_ids

EXAMPLES_DIR = Path(__file__).parent / "examples"
PROFILE_PATH = REPO_ROOT / "docs" / "modelling-profile.md"
OUTPUT_CONTRACT = (
    "Return exactly one IDS 1.0 XML document inside a single ```xml fenced block, and nothing else of "
    "substance."
)

AUTHORING_RULES = """\
You are the IDS author for NIYAM. You translate ONE rule unit from an Indian building bye-law into a
buildingSMART IDS 1.0 document that checks IFC4 models.

IDS 1.0 authoring rules:
1. Root element <ids> in namespace http://standards.buildingsmart.org/IDS. Declare
   xmlns:xs="http://www.w3.org/2001/XMLSchema" whenever you use xs:restriction.
2. Structure: <ids><info><title>...</title></info><specifications><specification name="..."
   ifcVersion="IFC4" identifier="<rule unit id>" description="<verbatim rule text>"
   instructions="<clause id>"><applicability minOccurs="0" maxOccurs="unbounded">...</applicability>
   <requirements>...</requirements></specification></specifications></ids>
3. Facets, in this order inside applicability and inside requirements: entity, partOf,
   classification, attribute, property, material.
   - entity: <name> is an upper-case IFC class (e.g. IFCWALL), optional <predefinedType>.
   - attribute: <name> and optional <value> of a direct IFC attribute (enumerations as their
     upper-case literal, e.g. NOTDEFINED).
   - property: <propertySet>, <baseName>, optional <value>, and a dataType attribute with the upper-case
     IFC measure type (e.g. IFCBOOLEAN, IFCLABEL, IFCLENGTHMEASURE). Quantity sets (Qto_...) are
     written as property facets too. Booleans are TRUE / FALSE.
4. A <value> holds either <simpleValue>...</simpleValue> or an
   <xs:restriction base="xs:string|xs:double|..."> with xs:enumeration, xs:pattern,
   xs:minInclusive, xs:maxInclusive, xs:minExclusive or xs:maxExclusive children.
5. Cardinality: a requirement facet has cardinality="required" (default), "optional" or
   "prohibited" (the matched value must NOT occur). Alternatively a whole specification is a
   prohibition when its applicability has maxOccurs="0": any element matching the applicability is
   a violation, and then no requirements are needed.
6. Units: numeric values in IDS are SI units (metres, square metres). Quantities and measure-typed
   properties are converted from the model's units before comparison, but IFC attributes are compared
   in raw file units (a 900 mm door has OverallWidth 900.0). NEVER put a numeric bound on an
   attribute facet; bound a Qto quantity or a measure-typed property instead.
7. Applicability must select exactly the elements the rule talks about, using only the conventions
   of the modelling profile below. Encode only the given rule unit, not the rest of the clause.
"""


def _examples_text() -> str:
    parts = ["EXAMPLES. These are synthetic illustrations of the format, not rules you are asked to encode:"]
    for path in sorted(EXAMPLES_DIR.glob("*.ids")):
        parts.append(f"--- {path.stem} ---\n```xml\n{path.read_text(encoding='utf-8').strip()}\n```")
    return "\n\n".join(parts)


def build_system_prompt() -> str:
    profile = PROFILE_PATH.read_text(encoding="utf-8").strip()
    return f"{AUTHORING_RULES}\n{profile}\n\n{_examples_text()}\n\nOUTPUT CONTRACT: {OUTPUT_CONTRACT}\n"


def build_user_message(unit: RuleUnit, clause: Clause) -> str:
    return (
        f"Source: {clause.source_doc}, clause {clause.id} (PDF page {clause.page}).\n"
        f"Parent clause text:\n<clause>\n{clause.text}\n</clause>\n\n"
        f"Rule unit {unit.id}:\n<rule>\n{unit.text}\n</rule>\n\n"
        f"Author an IDS 1.0 document for this rule unit only. Use identifier=\"{unit.id}\" and "
        f"instructions=\"{clause.id}\".\n{OUTPUT_CONTRACT}"
    )


def build_repair_message(previous: str, failure: StageResult) -> str:
    return (
        "The verifier rejected your previous answer.\n"
        f"Failing stage: {failure.stage}\n"
        f"Message: {failure.message}\n\n"
        f"Previous answer:\n```xml\n{previous}\n```\n\n"
        f"Fix the problem and return the complete corrected IDS document. {OUTPUT_CONTRACT}"
    )


def extract_xml(text: str) -> str | None:
    if m := re.search(r"```xml\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE):
        return m.group(1).strip()
    if m := re.search(r"<ids[\s>].*?</ids>", text, re.DOTALL):
        return m.group(0)
    return None


@dataclass
class Attempt:
    prompt_hash: str
    response_text: str
    extracted_xml: str | None
    gate: GateResult | None


@dataclass
class CompileResult:
    unit_id: str
    mode: Literal["gated", "baseline"]
    outcome: Literal["accepted", "needs_human", "extraction_failed", "baseline_scored"]
    model: str
    repair_rounds: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    wall_time_s: float = 0.0
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def _hash(system: str, messages: list[Message]) -> str:
    payload = json.dumps({"system": system, "messages": [asdict(m) for m in messages]}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


EXTRACTION_FAILURE = StageResult(
    "extraction", False, "no IDS document found: no ```xml fenced block and no <ids>...</ids> element"
)


def compile_unit(unit: RuleUnit, parent_clause: Clause, provider: LLMProvider, *, use_gate: bool = True,
                 max_repairs: int = 3, temperature: float = 0.0, max_tokens: int = 4096,
                 fixtures: FixturePair | None = None, run_dir: Path | None = None) -> CompileResult:
    started = time.perf_counter()
    fixtures = fixtures or fixture_pair(unit.id)
    system = build_system_prompt()
    messages = [Message("user", build_user_message(unit, parent_clause))]
    result = CompileResult(unit.id, "gated" if use_gate else "baseline", "needs_human", provider.model)

    while True:
        response = provider.complete(system, messages, temperature=temperature, max_tokens=max_tokens)
        result.model = response.model
        result.input_tokens += response.input_tokens
        result.output_tokens += response.output_tokens
        xml = extract_xml(response.text)
        gate = verify_ids(xml, unit, fixtures) if xml is not None else None
        result.attempts.append(Attempt(_hash(system, messages), response.text, xml, gate))

        if not use_gate:
            result.outcome = "baseline_scored" if xml is not None else "extraction_failed"
            break
        if gate is not None and gate.accepted:
            result.outcome = "accepted"
            break
        if result.repair_rounds == max_repairs:
            result.outcome = "needs_human" if xml is not None else "extraction_failed"
            break
        failure = gate.first_failure if gate is not None else EXTRACTION_FAILURE
        messages += [Message("assistant", response.text),
                     Message("user", build_repair_message(xml if xml is not None else response.text, failure))]
        result.repair_rounds += 1

    result.wall_time_s = time.perf_counter() - started
    if run_dir is not None:
        save_result(result, run_dir)
    return result


def save_result(result: CompileResult, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"{safe_name(result.unit_id)}__{result.mode}__{safe_name(result.model)}.json"
    data = asdict(result) | {"total_tokens": result.total_tokens}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
