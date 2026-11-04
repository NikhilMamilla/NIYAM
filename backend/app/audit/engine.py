"""Audit an IFC model against a rulepack. No LLM, no network.

Per rule and element of the rule's scope class:
  selector property absent             -> unchecked (cannot tell whether the rule applies)
  selector property present, different -> out_of_scope
  selected but any required data absent -> unchecked (never passed)
  otherwise                            -> passed / failed from running the rule's IDS with ifctester
"""

from collections import Counter
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
from ifctester import ids

from app.audit.models import AuditReport, Counts, ElementResult, RuleResult, Status
from app.rulepack.loader import Rulepack
from app.rulepack.models import RequiredData, Rule

NOT_STATED = (None, "", "NOTDEFINED")


class InvalidIfcError(Exception):
    """The file could not be read as an IFC model."""


def overall_status(counts: Counts) -> Status:
    if counts.failed:
        return "noncompliant"
    if counts.unchecked:
        return "incomplete"
    return "compliant" if counts.passed else "nothing_checked"


def _has(element, psets: dict, item: RequiredData) -> bool:
    if item.attribute:
        return getattr(element, item.attribute, None) not in NOT_STATED
    return psets.get(item.pset or item.qto, {}).get(item.name) is not None


def _ids_verdicts(spec_ids: ids.Ids, model) -> dict[str, tuple[str, str | None]]:
    """GlobalId -> (verdict, reason) for every element the IDS applies to."""
    spec_ids.validate(model)
    verdicts = {}
    for spec in spec_ids.specifications:
        if spec.maxOccurs == 0:  # prohibited specification: applying at all is the violation
            reason = "matches a prohibited specification: " + "; ".join(
                f.to_string("applicability") for f in spec.applicability)
            verdicts |= {e.GlobalId: ("failed", reason) for e in spec.applicable_entities}
            continue
        reasons: dict[str, list[str]] = {}
        for facet in spec.requirements:
            for failure in facet.failures:
                reasons.setdefault(failure["element"].GlobalId, []).append(
                    f"{failure['reason']} (requirement: {facet.to_string('requirement', spec, facet)})")
        for e in spec.applicable_entities:
            if e.GlobalId in reasons:
                verdicts[e.GlobalId] = ("failed", "; ".join(reasons[e.GlobalId]))
            elif verdicts.get(e.GlobalId, ("passed",))[0] != "failed":
                verdicts[e.GlobalId] = ("passed", None)
    return verdicts


def _audit_rule(model, rule: Rule, ids_xml: str) -> RuleResult:
    spec_ids = ids.from_string(ids_xml)
    prohibited = all(s.maxOccurs == 0 for s in spec_ids.specifications)
    ids_verdicts = _ids_verdicts(spec_ids, model)
    elements = []
    for e in model.by_type(rule.scope.ifc_class):
        psets = ifcopenshell.util.element.get_psets(e)
        verdict, reason = None, None
        sel = rule.scope.selector
        if sel is not None:
            value = psets.get(sel.pset, {}).get(sel.property)
            if value is None:
                verdict, reason = "unchecked", f"missing {sel.pset}.{sel.property}: cannot tell whether the rule applies"
            elif value != sel.value:
                verdict = "out_of_scope"
        if verdict is None:
            missing = [d.key.split(":", 1)[1] for d in rule.scope.required_data if not _has(e, psets, d)]
            if missing:
                verdict, reason = "unchecked", f"missing required data: {', '.join(missing)}"
            elif e.GlobalId in ids_verdicts:
                verdict, reason = ids_verdicts[e.GlobalId]
            elif prohibited:
                verdict = "passed"  # selected, complete, and not matched by the prohibition
            else:
                verdict, reason = "unchecked", "in scope but not matched by the rule's IDS applicability"
        elements.append(ElementResult(global_id=e.GlobalId, name=e.Name, ifc_class=e.is_a(),
                                      verdict=verdict, reason=reason))
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
    rules = [_audit_rule(model, rule, rulepack.ids_xml(rule)) for rule in rulepack.manifest.rules]
    summary = sum((r.counts for r in rules), Counts())
    return AuditReport(ifc_file=Path(ifc_path).name, ifc_schema=model.schema_identifier,
                       rulepack_version=rulepack.manifest.version, status=overall_status(summary),
                       summary=summary, rules=rules)
