"""BCF 2.1 export: one topic per failed and per unchecked element.

The element is referenced through a component-only viewpoint (a .bcfv with a Components/Selection
of its IfcGuid and no camera or snapshot), which is how BCF 2.1 attaches IFC GUIDs to a topic."""

import uuid
from pathlib import Path

from bcf.v2 import model as mdl
from bcf.v2.bcfxml import BcfXml
from bcf.v2.visinfo import VisualizationInfoHandler, build_components

from app.audit.models import AuditReport

PRIORITY = {"error": "High", "warning": "Normal"}
LABEL = {"failed": "violation", "unchecked": "unchecked"}


def _short(text: str, limit: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def export_bcf(report: AuditReport, path: Path) -> int:
    bcf = BcfXml.create_new(f"NIYAM audit of {report.ifc_file}")
    count = 0
    for rule in report.rules:
        for e in rule.elements:
            if e.verdict not in LABEL:
                continue
            description = (
                f"Rule {rule.unit_id}: {rule.rule_text}\n"
                f"Element: {e.name or '(unnamed)'} ({e.ifc_class}, GlobalId {e.global_id})\n"
                f"Verdict: {e.verdict}. Reason: {e.reason_plain}\n"
                f"Technical detail: {e.reason_raw}\n\n"
                f"Clause {rule.clause_id} ({rule.source_doc}, page {rule.page}):\n{rule.clause_text}"
                + ("" if rule.human_reviewed else "\n\nDraft rule encoding, not human-reviewed.")
            )
            topic = bcf.add_topic(f"[{rule.clause_id}] {_short(rule.rule_text)}", description, "NIYAM",
                                  "Issue", "Open")
            topic.topic.labels = [LABEL[e.verdict]]
            topic.topic.priority = PRIORITY.get(rule.severity, "Normal")
            topic.add_visinfo_handler(VisualizationInfoHandler(
                mdl.VisualizationInfo(guid=str(uuid.uuid4()), components=build_components(e.global_id))))
            count += 1
    bcf.save(str(path))
    return count
