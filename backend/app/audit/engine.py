"""Audit an IFC model against a rulepack. No LLM, no network.

Per rule and element of the rule's scope class:
  selector property absent             -> unchecked (cannot tell whether the rule applies)
  selector property present, different -> out_of_scope
  selected but any required data absent -> unchecked (never passed)
  otherwise                            -> passed / failed from running the rule's IDS with ifctester
"""

import re
from collections import Counter
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from ifctester import ids

from app.audit.models import AuditReport, Counts, ElementCounts, ElementResult, RuleResult, Status, Summary
from app.rulepack.loader import Rulepack
from app.rulepack.models import RequiredData, Rule

NOT_STATED = (None, "", "NOTDEFINED")
LENGTH_TYPES = {"IFCLENGTHMEASURE", "IFCPOSITIVELENGTHMEASURE", "IFCNONNEGATIVELENGTHMEASURE"}
BOUND_WORDS = {"minInclusive": "at least", "minExclusive": "more than",
               "maxInclusive": "at most", "maxExclusive": "less than"}
# Plain names for the modelling-profile data items (docs/modelling-profile.md)
DATA_PHRASES = {
    "pset:Pset_DoorCommon.FireExit": "whether it is an exit door",
    "qto:Qto_DoorBaseQuantities.Width": "declared width",
    "attribute:OperationType": "declared operation type",
}


class InvalidIfcError(Exception):
    """The file could not be read as an IFC model."""


class UnsupportedSchemaError(InvalidIfcError):
    """The file is IFC, but not the schema NIYAM audits."""


def overall_status(counts: Counts) -> Status:
    if counts.failed:
        return "noncompliant"
    if counts.unchecked:
        return "incomplete"
    return "compliant" if counts.passed else "nothing_checked"


def _words(identifier: str) -> str:
    """OperationType -> 'Operation type'; IfcDoor -> 'door'."""
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", identifier.removeprefix("Ifc"))
    return text[:1].upper() + text[1:].lower()


def _noun(element) -> str:
    return _words(element.is_a()).lower()


def _phrase(item: RequiredData) -> str:
    return DATA_PHRASES.get(item.key, f"value for {item.key.split(':', 1)[1]}")


def _has(element, psets: dict, item: RequiredData) -> bool:
    if item.attribute:
        return getattr(element, item.attribute, None) not in NOT_STATED
    return psets.get(item.pset or item.qto, {}).get(item.name) is not None


def _fallback(raw: str) -> str:
    return f"This element does not meet the rule's requirement. Details: {raw}"


def _prohibited_value_sentence(name: str, actual, options: list[str] | None) -> str:
    sentence = f"{_words(name)} is {actual}, which this rule does not allow"
    if options and len(options) > 1:
        sentence += f" (not allowed: {', '.join(options)})"
    return sentence + "."


def plain_failure_reason(facet, element, raw: str) -> str:
    """One sentence from the facet that failed and the element's actual values; never invents numbers."""
    value = facet.value
    if isinstance(facet, ids.Attribute) and facet.cardinality == "prohibited" and isinstance(facet.name, str):
        actual = getattr(element, facet.name, None)
        options = value.options.get("enumeration") if isinstance(value, ids.Restriction) else None
        if actual not in NOT_STATED:
            return _prohibited_value_sentence(facet.name, actual, options)
    if (isinstance(facet, ids.Property) and isinstance(value, ids.Restriction)
            and (facet.dataType or "").upper() in LENGTH_TYPES
            and isinstance(facet.propertySet, str) and isinstance(facet.baseName, str)):
        stored = ifcopenshell.util.element.get_psets(element).get(facet.propertySet, {}).get(facet.baseName)
        bounds = [(BOUND_WORDS[k], float(v)) for k, v in value.options.items() if k in BOUND_WORDS]
        if isinstance(stored, (int, float)) and bounds:
            metres = stored * ifcopenshell.util.unit.calculate_unit_scale(element.file)
            required = " and ".join(f"{word} {bound:g} m" for word, bound in bounds)
            return f"Declared {_words(facet.baseName).lower()} is {metres:g} m; this rule requires {required}."
    return _fallback(raw)


def _prohibited_spec_reason(spec, element, raw: str) -> str:
    sentences = [_prohibited_value_sentence(f.name, getattr(element, f.name, None), None)
                 for f in spec.applicability
                 if isinstance(f, ids.Attribute) and isinstance(f.name, str)
                 and getattr(element, f.name, None) not in NOT_STATED]
    return " ".join(sentences) or _fallback(raw)


def _ids_verdicts(spec_ids: ids.Ids, model) -> dict[str, tuple[str, str | None, str | None]]:
    """GlobalId -> (verdict, reason_raw, reason_plain) for every element the IDS applies to."""
    spec_ids.validate(model)
    verdicts = {}
    for spec in spec_ids.specifications:
        if spec.maxOccurs == 0:  # prohibited specification: applying at all is the violation
            raw = "matches a prohibited specification: " + "; ".join(
                f.to_string("applicability") for f in spec.applicability)
            for e in spec.applicable_entities:
                verdicts[e.GlobalId] = ("failed", raw, _prohibited_spec_reason(spec, e, raw))
            continue
        failures: dict[str, list[tuple[str, str]]] = {}
        for facet in spec.requirements:
            for failure in facet.failures:
                raw = f"{failure['reason']} (requirement: {facet.to_string('requirement', spec, facet)})"
                plain = plain_failure_reason(facet, failure["element"], raw)
                failures.setdefault(failure["element"].GlobalId, []).append((raw, plain))
        for e in spec.applicable_entities:
            if e.GlobalId in failures:
                raws, plains = zip(*failures[e.GlobalId])
                verdicts[e.GlobalId] = ("failed", "; ".join(raws), " ".join(plains))
            elif verdicts.get(e.GlobalId, ("passed",))[0] != "failed":
                verdicts[e.GlobalId] = ("passed", None, None)
    return verdicts


def _audit_rule(model, rule: Rule, ids_xml: str) -> RuleResult:
    spec_ids = ids.from_string(ids_xml)
    prohibited = all(s.maxOccurs == 0 for s in spec_ids.specifications)
    ids_verdicts = _ids_verdicts(spec_ids, model)
    elements = []
    for e in model.by_type(rule.scope.ifc_class):
        psets = ifcopenshell.util.element.get_psets(e)
        verdict, raw, plain = None, None, None
        sel = rule.scope.selector
        if sel is not None:
            value = psets.get(sel.pset, {}).get(sel.property)
            if value is None:
                key = f"{sel.pset}.{sel.property}"
                phrase = DATA_PHRASES.get(f"pset:{key}", f"a value for {key}")
                verdict = "unchecked"
                raw = f"missing {key}: cannot tell whether the rule applies"
                plain = f"This {_noun(e)} does not declare {phrase} ({key}), so it is unknown whether the rule applies."
            elif value != sel.value:
                verdict = "out_of_scope"
        if verdict is None:
            missing = [d for d in rule.scope.required_data if not _has(e, psets, d)]
            if missing:
                keys = [d.key.split(":", 1)[1] for d in missing]
                verdict = "unchecked"
                raw = f"missing required data: {', '.join(keys)}"
                plain = (f"This {_noun(e)} is in scope of the rule but has no "
                         f"{' or '.join(_phrase(d) for d in missing)} ({', '.join(keys)}), "
                         "so the rule could not be checked.")
            elif e.GlobalId in ids_verdicts:
                verdict, raw, plain = ids_verdicts[e.GlobalId]
            elif prohibited:
                verdict = "passed"  # selected, complete, and not matched by the prohibition
            else:
                verdict = "unchecked"
                raw = "in scope but not matched by the rule's IDS applicability"
                plain = f"This {_noun(e)} is in scope but the rule's check did not select it, so it was not checked."
        elements.append(ElementResult(global_id=e.GlobalId, express_id=e.id(), name=e.Name, ifc_class=e.is_a(),
                                      verdict=verdict, reason_plain=plain, reason_raw=raw))
    counts = Counts(**Counter(el.verdict for el in elements))
    return RuleResult(unit_id=rule.unit_id, clause_id=rule.clause_id, clause_text=rule.clause_text,
                      rule_text=rule.rule_text, source_doc=rule.source_doc, page=rule.page,
                      severity=rule.severity, human_reviewed=rule.human_reviewed,
                      status=overall_status(counts), counts=counts, elements=elements)


def audit(ifc_path: Path, rulepack: Rulepack) -> AuditReport:
    try:
        model = ifcopenshell.open(str(ifc_path))
    except (ifcopenshell.Error, OSError, RuntimeError) as e:
        raise InvalidIfcError(f"could not read IFC file: {e}") from e
    if model.schema != "IFC4":
        raise UnsupportedSchemaError(f"unsupported IFC schema {model.schema_identifier}: NIYAM v0.1 audits IFC4 models")
    rules = [_audit_rule(model, rule, rulepack.ids_xml(rule)) for rule in rulepack.manifest.rules]
    checks = sum((r.counts for r in rules), Counts())
    return AuditReport(ifc_file=Path(ifc_path).name, ifc_schema=model.schema_identifier,
                       rulepack_version=rulepack.manifest.version, status=overall_status(checks),
                       summary=Summary(checks=checks, elements=_element_counts(model, rulepack, rules)), rules=rules)


def _element_counts(model, rulepack: Rulepack, rules: list[RuleResult]) -> ElementCounts:
    scoped = {e.id() for c in {r.scope.ifc_class for r in rulepack.manifest.rules} for e in model.by_type(c)}
    verdicts: dict[int, set[str]] = {}
    for r in rules:
        for e in r.elements:
            verdicts.setdefault(e.express_id, set()).add(e.verdict)
    with_failed = sum("failed" in v for v in verdicts.values())
    with_unchecked = sum("failed" not in v and "unchecked" in v for v in verdicts.values())
    return ElementCounts(total_in_model_of_scoped_classes=len(scoped), with_failed=with_failed,
                         with_unchecked=with_unchecked, clean=len(scoped) - with_failed - with_unchecked)
