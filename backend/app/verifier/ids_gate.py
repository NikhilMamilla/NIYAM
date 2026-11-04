"""IDS verifier gate: accept a candidate IDS for a rule unit only if it is valid and its verdicts on
the unit's pass/fail fixture pair are exactly right. Stops at the first failing stage."""

from dataclasses import dataclass
from xml.etree import ElementTree as ET

import ifcopenshell
from ifctester import ids
from xmlschema.validators.exceptions import XMLSchemaValidationError

from app.corpus.models import RuleUnit
from app.fixtures.builders import FixturePair

STAGES = [
    "xml_wellformed",
    "xsd_valid",
    "loads_in_ifctester",
    "applicable_on_fixtures",
    "verdict_pass_fixture",
    "verdict_fail_fixture",
]


@dataclass
class StageResult:
    stage: str
    passed: bool
    message: str


@dataclass
class GateResult:
    accepted: bool
    stage_results: list[StageResult]
    first_failure: StageResult | None  # what a repair loop should be told


class _Rejected(Exception):
    pass


def _run(spec_ids: ids.Ids, path) -> list[dict]:
    spec_ids.validate(ifcopenshell.open(str(path)))
    return [
        {
            "name": s.name,
            "status": s.status,
            "applicable": len(s.applicable_entities),
            "failed": {e.GlobalId for e in s.failed_entities},
        }
        for s in spec_ids.specifications
    ]


def verify_ids(candidate_xml: str, unit: RuleUnit, fixtures: FixturePair) -> GateResult:
    results: list[StageResult] = []

    def stage(name, check):
        try:
            message = check()
        except _Rejected as e:
            results.append(StageResult(name, False, str(e)))
            raise
        results.append(StageResult(name, True, message))
        return message

    def wellformed():
        try:
            ET.fromstring(candidate_xml)
        except ET.ParseError as e:
            raise _Rejected(f"XML is not well-formed: {e}")
        return "parsed"

    def xsd_valid():
        # Validate the raw text, as ids.open(path, validate=True) does. ids.from_string(validate=True)
        # goes through an ElementTree that drops the xs: prefix, so every xs:restriction would fail.
        try:
            ids.get_schema().validate(candidate_xml)
        except XMLSchemaValidationError as e:
            raise _Rejected(f"IDS 1.0 XSD violation at {e.path}: {e.reason}")
        return "valid against IDS 1.0 XSD"

    loaded = {}

    def loads():
        try:
            loaded["ids"] = ids.from_string(candidate_xml)
        except Exception as e:  # any loader error is feedback for the author, not a gate crash
            raise _Rejected(f"ifctester could not load the IDS: {type(e).__name__}: {e}")
        if not loaded["ids"].specifications:
            raise _Rejected("IDS contains no specifications")
        return f"{len(loaded['ids'].specifications)} specification(s)"

    runs = {}

    def applicable():
        for kind, path in (("pass", fixtures.pass_path), ("fail", fixtures.fail_path)):
            runs[kind] = _run(loaded["ids"], path)
            for r in runs[kind]:
                if r["applicable"] == 0:
                    raise _Rejected(
                        f"specification {r['name']!r} applies to 0 entities in {path.name}; "
                        "a specification that applies to nothing passes vacuously"
                    )
        return "; ".join(f"{k}: {[r['applicable'] for r in v]} applicable" for k, v in runs.items())

    def verdict_pass():
        bad = [r for r in runs["pass"] if not r["status"]]
        if bad:
            raise _Rejected(
                f"must pass {fixtures.pass_path.name} but failed: "
                + "; ".join(f"{r['name']!r} failed {sorted(r['failed'])}" for r in bad)
            )
        return f"passes {fixtures.pass_path.name}"

    def verdict_fail():
        if all(r["status"] for r in runs["fail"]):
            raise _Rejected(f"must fail {fixtures.fail_path.name} but passed it (spec too lenient)")
        failed = set().union(*(r["failed"] for r in runs["fail"]))
        if failed != fixtures.expected_failing:
            raise _Rejected(
                f"failing entities {sorted(failed)} != expected {sorted(fixtures.expected_failing)}"
            )
        return f"fails {fixtures.fail_path.name} on exactly {sorted(failed)}"

    checks = [wellformed, xsd_valid, loads, applicable, verdict_pass, verdict_fail]
    try:
        for name, check in zip(STAGES, checks):
            stage(name, check)
    except _Rejected:
        pass
    first_failure = next((r for r in results if not r.passed), None)
    return GateResult(accepted=first_failure is None, stage_results=results, first_failure=first_failure)
