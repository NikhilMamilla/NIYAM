"""Self-contained HTML audit report: inline CSS, no scripts, no external assets; all text escaped."""

from html import escape

from app.audit.models import AuditReport, ElementResult, RuleResult

CSS = """
body{font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:24px 16px;color:#1d1d1f;background:#fff}
h1{font-size:24px;margin:0 0 4px}h2{font-size:19px;margin:32px 0 6px}h3{font-size:15px;margin:18px 0 6px}
.meta{color:#555}.note{background:#fff6e0;border:1px solid #e9c46a;padding:8px 12px;border-radius:6px}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-weight:600;font-size:13px}
.noncompliant{background:#fde2e1;color:#9b1c1c}.incomplete{background:#fff1c2;color:#7a5200}
.compliant{background:#dcf5e3;color:#11612f}.nothing_checked{background:#e8e8ed;color:#444}
table{border-collapse:collapse;width:100%;margin:6px 0 12px;font-size:14px}
th,td{border:1px solid #d8d8de;padding:5px 8px;text-align:left;vertical-align:top}th{background:#f3f3f6}
pre{white-space:pre-wrap;background:#f6f6f8;padding:10px 12px;border-radius:6px;font:13px/1.45 ui-monospace,monospace}
code{font:13px ui-monospace,monospace}
"""


def _e(value) -> str:
    return escape("" if value is None else str(value), quote=True)


def _badge(status: str) -> str:
    return f'<span class="badge {_e(status)}">{_e(status)}</span>'


def _counts_row(label: str, c, status: str) -> str:
    return (f"<tr><td>{label}</td><td>{_badge(status)}</td><td>{c.passed}</td><td>{c.failed}</td>"
            f"<td>{c.unchecked}</td><td>{c.out_of_scope}</td></tr>")


def _element_table(elements: list[ElementResult]) -> str:
    rows = "".join(
        f"<tr><td>{_e(e.name)}</td><td>{_e(e.ifc_class)}</td><td><code>{_e(e.global_id)}</code></td>"
        f"<td>{_e(e.reason)}</td></tr>" for e in elements)
    return f"<table><tr><th>Name</th><th>Class</th><th>GlobalId</th><th>Reason</th></tr>{rows}</table>"


def _rule_section(r: RuleResult) -> str:
    parts = [
        f"<h2>{_e(r.unit_id)} {_badge(r.status)}</h2>",
        f'<p class="meta">Clause {_e(r.clause_id)}, {_e(r.source_doc)} page {_e(r.page)} &middot; '
        f"severity {_e(r.severity)} &middot; {'human-reviewed' if r.human_reviewed else 'draft rule, not human-reviewed'}"
        f" &middot; passed {r.counts.passed}, failed {r.counts.failed}, unchecked {r.counts.unchecked}, "
        f"out of scope {r.counts.out_of_scope}</p>",
        f"<p><strong>Rule:</strong> {_e(r.rule_text)}</p>",
        f"<h3>Clause text</h3><pre>{_e(r.clause_text)}</pre>",
    ]
    for verdict, heading in (("failed", "Failed elements"), ("unchecked", "Unchecked elements (missing data)")):
        elements = [e for e in r.elements if e.verdict == verdict]
        parts.append(f"<h3>{heading} ({len(elements)})</h3>")
        parts.append(_element_table(elements) if elements else "<p>None.</p>")
    return "\n".join(parts)


def render_html(report: AuditReport) -> str:
    drafts = [r.unit_id for r in report.rules if not r.human_reviewed]
    note = (f'<p class="note">Rules {_e(", ".join(drafts))} are draft encodings and not human-reviewed. '
            "Unchecked elements lack the data a rule needs; they are not passes.</p>") if drafts else ""
    rows = "".join(_counts_row(_e(r.unit_id), r.counts, r.status) for r in report.rules)
    rows += _counts_row("<strong>overall</strong>", report.summary, report.status)
    body = "\n".join(_rule_section(r) for r in report.rules)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NIYAM audit report</title><style>{CSS}</style></head><body>
<h1>NIYAM audit report {_badge(report.status)}</h1>
<p class="meta">Model <code>{_e(report.ifc_file)}</code> ({_e(report.ifc_schema)}) &middot; rulepack {_e(report.rulepack_version)}</p>
{note}
<table><tr><th>Rule</th><th>Status</th><th>Passed</th><th>Failed</th><th>Unchecked</th><th>Out of scope</th></tr>{rows}</table>
{body}
</body></html>
"""
