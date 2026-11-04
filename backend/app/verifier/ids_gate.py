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
    "unit_safe_bounds",
    "loads_in_ifctester",
    "applicable_on_fixtures",
    "verdict_pass_fixture",
    "verdict_fail_fixture",
]
IDS_NS = "{http://standards.buildingsmart.org/IDS}"
XS_NS = "{http://www.w3.org/2001/XMLSchema}"
NUMERIC_BOUNDS = ("minInclusive", "maxInclusive", "minExclusive", "maxExclusive")


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


def _label(model, global_id: str) -> str:
    try:
        return model.by_guid(global_id).Name or global_id
    except RuntimeError:
        return global_id


def _labels(model, global_ids) -> list[str]:
    return sorted(_label(model, g) for g in global_ids)


def _run(spec_ids: ids.Ids, model) -> list[dict]:
    spec_ids.validate(model)
    runs = []
    for s in spec_ids.specifications:
        prohibited = s.maxOccurs == 0
        failed = {e.GlobalId for e in s.failed_entities}
        if prohibited:  # ifctester only sets status=False; every applicable entity is a violation
            failed |= {e.GlobalId for e in s.applicable_entities}
        # snapshot: validating the next model resets status on the same Specification objects
        runs.append({"name": s.name, "status": s.status, "prohibited": prohibited,
                     "applicable": len(s.applicable_entities), "failed": failed})
    return runs


def _attribute_bounds(candidate_xml: str) -> list[str]:
    offenders = []
    for attribute in ET.fromstring(candidate_xml).iter(f"{IDS_NS}attribute"):
        name = attribute.findtext(f"{IDS_NS}name/{IDS_NS}simpleValue") or "(restricted name)"
        for restriction in attribute.iter(f"{XS_NS}restriction"):
            for bound in restriction:
                tag = bound.tag.removeprefix(XS_NS)
                if tag in NUMERIC_BOUNDS:
                    offenders.append(f"{name} ({tag} {bound.get('value')})")
    return offenders


def verify_ids(candidate_xml: str, unit: RuleUnit, fixtures: FixturePair) -> GateResult:
    results: list[StageResult] = []

    def stage(name, check):
        try:
            message = check()
        except _Rejected as e:
            results.append(StageResult(name, False, str(e)))
            raise
        except Exception as e:  # candidates are untrusted LLM output; ifctester may raise on odd input
            results.append(StageResult(name, False, f"ifctester raised {type(e).__name__}: {e}"))
            raise _Rejected(str(e)) from e
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

    def unit_safe_bounds():
        offenders = _attribute_bounds(candidate_xml)
        if offenders:
            raise _Rejected(
                f"numeric bound on an IFC attribute: {', '.join(offenders)}. Attribute values are compared "
                "in raw file units (in a millimetre model a 900 mm door reads 900.0, so 'minInclusive 1.0' "
                "passes), while quantities and measure-typed properties are converted to SI metres. Put the "
                "bound on a Qto quantity (e.g. Qto_DoorBaseQuantities.Width, dataType IFCLENGTHMEASURE) or a "
                "measure-typed property facet instead of the attribute."
            )
        return "no numeric bounds on attributes"

    loaded = {}

    def loads():
        # Defensive: no test triggers this stage; every XSD-valid input tried so far loads.
        try:
            loaded["ids"] = ids.from_string(candidate_xml)
        except Exception as e:  # any loader error is feedback for the author, not a gate crash
            raise _Rejected(f"ifctester could not load the IDS: {type(e).__name__}: {e}")
        if not loaded["ids"].specifications:
            raise _Rejected("IDS contains no specifications")
        return f"{len(loaded['ids'].specifications)} specification(s)"

    models = {"pass": ifcopenshell.open(str(fixtures.pass_path)), "fail": ifcopenshell.open(str(fixtures.fail_path))}
    paths = {"pass": fixtures.pass_path, "fail": fixtures.fail_path}
    runs = {}

    def applicable():
        for kind, model in models.items():
            candidates = model.by_type("IfcRoot")
            for spec in loaded["ids"].specifications:
                # Each applicability facet must match something on its own. Their conjunction may
                # legitimately be empty, e.g. a maxOccurs=0 spec on a fixture with no violation.
                for facet in spec.applicability:
                    if not any(bool(facet(e)) for e in candidates):
                        raise _Rejected(
                            f"in specification {spec.name!r} the applicability facet "
                            f"'{facet.to_string('applicability')}' matches no entity in {paths[kind].name}; "
                            "check class, property set, property name and value spelling"
                        )
            runs[kind] = _run(loaded["ids"], model)
            for r in runs[kind]:
                if r["applicable"] == 0 and not r["prohibited"]:
                    raise _Rejected(
                        f"specification {r['name']!r} applies to 0 entities in {paths[kind].name}; "
                        "a specification that applies to nothing passes vacuously"
                    )
        return "; ".join(f"{k}: {[r['applicable'] for r in v]} applicable" for k, v in runs.items())

    def verdict_pass():
        bad = [r for r in runs["pass"] if not r["status"]]
        if bad:
            raise _Rejected(
                f"must pass {paths['pass'].name} but failed: "
                + "; ".join(f"{r['name']!r} failed {_labels(models['pass'], r['failed'])}" for r in bad)
            )
        return f"passes {paths['pass'].name}"

    def verdict_fail():
        if all(r["status"] for r in runs["fail"]):
            raise _Rejected(f"must fail {paths['fail'].name} but passed it (spec too lenient)")
        failed = set().union(*(r["failed"] for r in runs["fail"]))
        if failed != fixtures.expected_failing:
            raise _Rejected(
                f"failing entities {_labels(models['fail'], failed)} != expected "
                f"{_labels(models['fail'], fixtures.expected_failing)}"
            )
        return f"fails {paths['fail'].name} on exactly {_labels(models['fail'], failed)}"

    checks = [wellformed, xsd_valid, unit_safe_bounds, loads, applicable, verdict_pass, verdict_fail]
    try:
        for name, check in zip(STAGES, checks):
            stage(name, check)
    except _Rejected:
        pass
    first_failure = next((r for r in results if not r.passed), None)
    return GateResult(accepted=first_failure is None, stage_results=results, first_failure=first_failure)
