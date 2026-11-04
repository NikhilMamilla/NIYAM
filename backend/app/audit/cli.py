import argparse
import sys
from pathlib import Path

from app.audit.bcf_export import export_bcf
from app.audit.engine import InvalidIfcError, audit
from app.audit.models import AuditReport
from app.audit.report_html import render_html
from app.rulepack.loader import DEFAULT_PACK, load_rulepack


def print_summary(report: AuditReport) -> None:
    print(f"{report.ifc_file} ({report.ifc_schema}), rulepack {report.rulepack_version}")
    print(f"{'rule':18} {'status':16} {'passed':>6} {'failed':>6} {'unchecked':>9} {'out_of_scope':>12}")
    for r in report.rules:
        c = r.counts
        print(f"{r.unit_id:18} {r.status:16} {c.passed:>6} {c.failed:>6} {c.unchecked:>9} {c.out_of_scope:>12}")
    s, e = report.summary.checks, report.summary.elements
    print(f"{'overall checks':18} {report.status:16} {s.passed:>6} {s.failed:>6} {s.unchecked:>9} {s.out_of_scope:>12}")
    print(f"{report.element_noun()} affected: {e.with_failed} with violations, {e.with_unchecked} could not be "
          f"fully checked, {e.clean} clean (of {e.total_in_model_of_scoped_classes})")


def write_outputs(report: AuditReport, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "report.html").write_text(render_html(report), encoding="utf-8")
    export_bcf(report, out_dir / "issues.bcf")
    return [out_dir / n for n in ("report.json", "report.html", "issues.bcf")]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.audit.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("ifc", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    args = parser.parse_args(argv)
    try:
        report = audit(args.ifc, load_rulepack(args.pack))
    except InvalidIfcError as e:
        print(f"error: {e}")
        return 2
    print_summary(report)
    if args.out:
        for path in write_outputs(report, args.out):
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
