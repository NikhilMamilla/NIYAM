import re
import zipfile

import pytest
from bcf.v2.bcfxml import BcfXml

from app.audit.bcf_export import export_bcf
from app.audit.engine import audit
from app.audit.models import AuditReport, Counts, ElementCounts, ElementResult, RuleResult, Summary
from app.audit.report_html import render_html
from app.fixtures.samples import SAMPLES_DIR
from app.rulepack.loader import load_rulepack


@pytest.fixture(scope="module")
def report():
    return audit(SAMPLES_DIR / "sample_a_mm.ifc", load_rulepack())


def issues(report):
    return [(r, e) for r in report.rules for e in r.elements if e.verdict in ("failed", "unchecked")]


# --- HTML -----------------------------------------------------------------------


def test_html_is_self_contained(report):
    html = render_html(report)
    assert html.startswith("<!doctype html>")
    assert "<script" not in html.lower()
    assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", html, re.IGNORECASE)
    assert "<link" not in html.lower() and "@import" not in html


def test_html_shows_summary_clauses_and_issue_tables(report):
    html = render_html(report)
    assert "noncompliant" in html
    for r in report.rules:
        assert r.clause_id in html and r.unit_id in html
    assert "5.4.1 Doorways" in html and "No exit doorway shall be less than 1m in width." in html
    for r, e in issues(report):
        assert e.global_id in html
    assert "A-1-06 exit without width quantity" in html
    assert "missing required data: Qto_DoorBaseQuantities.Width" in html  # raw reason
    assert "Declared width is 0.9 m; this rule requires at least 1 m." in html  # plain reason
    assert "not human-reviewed" in html
    # rule x element checks and distinct elements are labelled apart (sample A: 12 doors, 5 + 3 affected)
    assert "Checks run: passed 17, failed 6, unchecked 7, out of scope 6" in html
    assert "Doors affected: 5 with violations, 3 could not be fully checked (of 12 in scope classes)" in html


def test_html_escapes_all_dynamic_text():
    evil = "<script>alert(1)</script>"
    rule = RuleResult(
        unit_id="X#1", clause_id="X", clause_text=f"clause {evil}", rule_text=f"rule {evil}", source_doc="d",
        page=1, severity="error", human_reviewed=True, status="noncompliant", counts=Counts(failed=1),
        elements=[ElementResult(global_id="g'\"&", express_id=1, name=evil, ifc_class="IfcDoor", verdict="failed", reason_plain=evil, reason_raw=evil)])
    report = AuditReport(ifc_file=f"{evil}.ifc", ifc_schema="IFC4", rulepack_version="v0", status="noncompliant",
                         summary=Summary(checks=Counts(failed=1), elements=ElementCounts(
                             total_in_model_of_scoped_classes=1, with_failed=1)), rules=[rule])
    html = render_html(report)
    assert "<script" not in html.lower()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "g&#x27;&quot;&amp;" in html


# --- BCF ------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bcf_path(report, tmp_path_factory):
    path = tmp_path_factory.mktemp("bcf") / "issues.bcf"
    export_bcf(report, path)
    return path


def test_bcf_zip_structure(report, bcf_path):
    with zipfile.ZipFile(bcf_path) as z:
        names = z.namelist()
        assert "bcf.version" in names
        assert 'VersionId="2.1"' in z.read("bcf.version").decode()
        markups = [n for n in names if n.endswith("/markup.bcf")]
        assert len(markups) == len(issues(report))
        assert not [n for n in names if n.lower().endswith((".png", ".jpg"))]  # no snapshots


def test_bcf_topics_read_back(report, bcf_path):
    bcf = BcfXml.load(bcf_path)
    topics = list(bcf.topics.values())
    assert len(topics) == len(issues(report)) == report.summary.checks.failed + report.summary.checks.unchecked

    by_guid = {}
    for t in topics:
        [viewpoint] = t.viewpoints.values()
        [guid] = viewpoint.get_selected_guids()
        by_guid.setdefault(guid, []).append(t)
        assert viewpoint.visualization_info.perspective_camera is None  # component-only, no camera

    for rule, element in issues(report):
        [topic] = [t for t in by_guid[element.global_id] if t.topic.title.startswith(f"[{rule.clause_id}]")
                   and rule.rule_text[:30] in t.topic.title]
        expected_label = "violation" if element.verdict == "failed" else "unchecked"
        assert topic.topic.labels == [expected_label]
        assert topic.topic.priority == "High"
        assert "Audit summary: 6 failed checks on 5 distinct doors; 3 more doors could not be fully checked."             in topic.topic.description
        assert rule.clause_text in topic.topic.description
        assert element.reason_plain in topic.topic.description and element.reason_raw in topic.topic.description
        assert element.global_id in topic.topic.description
