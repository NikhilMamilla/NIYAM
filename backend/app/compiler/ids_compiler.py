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

import ifcopenshell

from app.corpus.models import Clause, RuleUnit
from app.fixtures.builders import REPO_ROOT, FixturePair, fixture_pair, safe_name
from app.geometry import helpers as geo_helpers
from app.llm.base import LLMProvider, Message
from app.verifier import geometric_gate
from app.verifier.geometric_gate import verify_geometric
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


GEOMETRIC_OUTPUT_CONTRACT = (
    "Return exactly one Python module inside a single ```python fenced block, and nothing else of substance."
)


def _helper_reference() -> str:
    """The helper API, read from app/geometry/helpers.py so this text cannot drift from the code."""
    return "\n".join(f"- helpers.{s.name}{s.signature}\n  {s.doc.replace(chr(10), chr(10) + '  ')}"
                     for s in geo_helpers.signatures())


def _geometric_rules() -> str:
    forbidden = " ".join(sorted(geometric_gate.FORBIDDEN_NAMES))
    return f"""\
You are the geometric-check author for NIYAM. You translate ONE rule unit from an Indian building bye-law
into a small Python function that checks IFC4 models using values computed from their geometry.

The check contract:
1. Return one module containing optionally `import math`, an optional docstring and exactly one function
   `def check(model, helpers):` that returns a list of findings. Nothing else at the top level.
2. Use ONLY the `helpers` object for model access. Every helper returns SI values (metres, m2) or None when the
   value cannot be computed. Never guess a value; None means the element is `unchecked`.
3. Create findings with helpers.finding(element, verdict, detail, measured=None, required=None) where verdict is
   "pass", "fail" or "unchecked". `detail` is one plain sentence with the numbers, for example
   "Computed floor area is 7.20 m2; this rule requires at least 9.50 m2." Compare with a 1e-9 tolerance so a
   value exactly at the bound passes.
4. Return a finding for each element the rule applies to and for each element whose applicability cannot be
   decided (missing selection data -> "unchecked"). Return NO finding for elements the rule does not apply to:
   the audit reports those as out of scope.
5. "unchecked" is only for missing data. Never use it to avoid deciding, and never report "pass" for an element
   whose value is missing.
6. The code is statically scanned and run in an isolated process. Do not use these names or attributes: {forbidden}.
   Do not use any name or attribute that starts and ends with two underscores, str.format, classes, try/except,
   with, or imports other than `import math`. Loops, comprehensions and f-strings are fine.

Helper API (call as helpers.<name>(...)):
{_helper_reference()}
"""


def _geometric_examples_text() -> str:
    parts = ["EXAMPLES. These are synthetic illustrations of the format, not rules you are asked to encode:"]
    for path in sorted(EXAMPLES_DIR.glob("geo_*.py")):
        parts.append(f"--- {path.stem} ---\n```python\n{path.read_text(encoding='utf-8').strip()}\n```")
    return "\n\n".join(parts)


def build_system_prompt(unit: RuleUnit | None = None) -> str:
    profile = PROFILE_PATH.read_text(encoding="utf-8").strip()
    if unit is not None and unit.tier == "geometric":
        return (f"{_geometric_rules()}\n{profile}\n\n{_geometric_examples_text()}\n\n"
                f"OUTPUT CONTRACT: {GEOMETRIC_OUTPUT_CONTRACT}\n")
    return f"{AUTHORING_RULES}\n{profile}\n\n{_examples_text()}\n\nOUTPUT CONTRACT: {OUTPUT_CONTRACT}\n"


def build_user_message(unit: RuleUnit, clause: Clause) -> str:
    head = (
        f"Source: {clause.source_doc}, clause {clause.id} (PDF page {clause.page}).\n"
        f"Parent clause text:\n<clause>\n{clause.text}\n</clause>\n\n"
        f"Rule unit {unit.id}:\n<rule>\n{unit.text}\n</rule>\n\n"
    )
    if unit.tier == "geometric":
        return (head + "Author the Python check for this rule unit only, using the modelling profile's "
                f"conventions to select the elements.\n{GEOMETRIC_OUTPUT_CONTRACT}")
    return (head + f"Author an IDS 1.0 document for this rule unit only. Use identifier=\"{unit.id}\" and "
            f"instructions=\"{clause.id}\".\n{OUTPUT_CONTRACT}")


MUST_FAIL = "the element that must FAIL in the non-compliant model"
MUST_PASS = "a control element that must PASS"


def mask_fixture_details(message: str, fixtures: FixturePair) -> str:
    """Replace fixture file names, element names and GlobalIds with role labels.

    The gate keeps full detail for humans; the model only learns which verdict was wrong."""
    replacements = {fixtures.pass_path.name: "the compliant model", fixtures.fail_path.name: "the non-compliant model"}
    for path in (fixtures.pass_path, fixtures.fail_path):
        for e in ifcopenshell.open(str(path)).by_type("IfcRoot"):
            role = MUST_FAIL if e.GlobalId in fixtures.expected_failing else MUST_PASS
            replacements[e.GlobalId] = role
            if (e.is_a("IfcElement") or e.is_a("IfcSpace")) and e.Name:  # not storeys: "Building" is a common word
                replacements[e.Name] = role
    for token in sorted(replacements, key=len, reverse=True):  # longest first: no partial overlaps
        message = message.replace(token, replacements[token])
    return message


def build_repair_message(previous: str, failure: StageResult, fixtures: FixturePair, tier: str = "ids") -> str:
    geometric = tier == "geometric"
    return (
        "The verifier rejected your previous answer.\n"
        f"Failing stage: {failure.stage}\n"
        f"Message: {mask_fixture_details(failure.message, fixtures)}\n\n"
        f"Previous answer:\n```{'python' if geometric else 'xml'}\n{previous}\n```\n\n"
        + ("Fix the problem and return the complete corrected Python module. " + GEOMETRIC_OUTPUT_CONTRACT
           if geometric else f"Fix the problem and return the complete corrected IDS document. {OUTPUT_CONTRACT}")
    )


def extract_python(text: str) -> str | None:
    if m := re.search(r"```(?:python|py)\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE):
        return m.group(1).strip()
    return None


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
GEOMETRIC_EXTRACTION_FAILURE = StageResult("extraction", False, "no Python code found: no ```python fenced block")


def compile_unit(unit: RuleUnit, parent_clause: Clause, provider: LLMProvider, *, use_gate: bool = True,
                 max_repairs: int = 3, temperature: float = 0.0, max_tokens: int = 4096,
                 fixtures: FixturePair | None = None, run_dir: Path | None = None) -> CompileResult:
    started = time.perf_counter()
    fixtures = fixtures or fixture_pair(unit.id)
    geometric = unit.tier == "geometric"
    extract = extract_python if geometric else extract_xml
    verify = verify_geometric if geometric else verify_ids
    extraction_failure = GEOMETRIC_EXTRACTION_FAILURE if geometric else EXTRACTION_FAILURE
    system = build_system_prompt(unit)
    messages = [Message("user", build_user_message(unit, parent_clause))]
    result = CompileResult(unit.id, "gated" if use_gate else "baseline", "needs_human", provider.model)

    while True:
        response = provider.complete(system, messages, temperature=temperature, max_tokens=max_tokens)
        result.model = response.model
        result.input_tokens += response.input_tokens
        result.output_tokens += response.output_tokens
        xml = extract(response.text)  # the candidate: an IDS document, or Python source for a geometric unit
        gate = verify(xml, unit, fixtures) if xml is not None else None
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
        failure = gate.first_failure if gate is not None else extraction_failure
        messages += [Message("assistant", response.text),
                     Message("user", build_repair_message(xml if xml is not None else response.text, failure,
                                                          fixtures, unit.tier))]
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
