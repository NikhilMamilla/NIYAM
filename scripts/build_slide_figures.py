"""Write the two slide figures as SVG into submission/screens/ (the PNGs are rendered from them by
frontend/e2e/shots.spec.ts):

- 07-results-chart.svg: run 2, wrong_shipped and held-out correct per model, gated vs ungated, each a dot with its
  Wilson 95% interval and the harness's own label (read verbatim from eval/results/<run>/summary.md);
- 08-pipeline.svg: the pipeline, with counts from the committed files (via scripts/check_numbers.py facts).

Usage (repository root): python scripts/build_slide_figures.py"""

import csv
import importlib.util
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission" / "screens"
RUN = "20261118T140452Z-5b7edb"
INK, INK2, INK3, RULE, PAPER = "#191F30", "#3D4559", "#5A6478", "#C8BFA3", "#F5F0E4"
GATED, UNGATED, UNGATED_EDGE = "#3447C7", "#D99A1E", "#8A5200"  # the landing page's chart tones (validated pair)
FONT = "IBM Plex Sans, Segoe UI, Arial, sans-serif"


def harness_cells() -> dict[tuple[str, str], dict[str, str]]:
    """The 'All units' item table of summary.md: {(model, mode): {column: cell}}, cells exactly as written."""
    md = (ROOT / "eval/results" / RUN / "summary.md").read_text(encoding="utf-8")
    table = md.split("## All units", 1)[1].split("\n\n### Paired", 1)[0]
    rows = [r.strip("|").split(" | ") for r in table.splitlines() if r.startswith("| nemotron")]
    head = ["model", "mode", "n", "valid", "dev_correct", "heldout_correct", "shipped", "wrong_shipped", "needs_human"]
    return {(r[0].strip(), r[1]): dict(zip(head, (c.strip() for c in r))) for r in rows}


def rates() -> dict[tuple[str, str, str], tuple[float, float, float]]:
    with open(ROOT / "eval/results" / RUN / "summary.csv", encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["view"] == "all_units"]
    return {(r["model"], r["mode"], m): (float(r[f"{m}_rate"]), float(r[f"{m}_lo"]), float(r[f"{m}_hi"]))
            for r in rows for m in ("wrong_shipped", "heldout_correct")}


def results_chart() -> str:
    cells, r = harness_cells(), rates()
    models = sorted({m for m, _ in cells})
    W, H, left, panel_w, gap, top, row_h = 1600, 900, 360, 520, 110, 250, 70
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
           f'<text x="60" y="80" font-size="38" fill="{INK}" font-weight="600">With the gate, far fewer wrong rules reach the rulepack</text>',
           f'<text x="60" y="122" font-size="22" fill="{INK2}">Run 2 ({RUN}): 25 MBBL units x 3 repeats = 75 attempts per model and mode; '
           'dot = rate, bar = Wilson 95% interval</text>',
           f'<text x="60" y="158" font-size="18" fill="{INK3}">Models: nemotron-3-ultra-550b-a55b and nemotron-3.5-lightning-30b-a3b (NVIDIA, open), temperature 0.0</text>']
    for p, (metric, title) in enumerate([("wrong_shipped", "wrong_shipped: wrong on held-out / shipped (lower is better)"),
                                         ("heldout_correct", "Held-out correct / all attempts (higher is better)")]):
        x0 = left + p * (panel_w + gap)
        out.append(f'<text x="{x0}" y="{top - 30}" font-size="21" fill="{INK}" font-weight="600">{escape(title)}</text>')
        for t in range(0, 101, 25):
            x = x0 + panel_w * t / 100
            out.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + row_h * 4 + 10}" stroke="{RULE}" stroke-width="1"/>')
            out.append(f'<text x="{x}" y="{top + row_h * 4 + 40}" font-size="18" fill="{INK3}" text-anchor="middle">{t}%</text>')
        i = 0
        for model in models:
            for mode in ("gated", "ungated"):
                y = top + 30 + row_h * i
                rate, lo, hi = r[(model, mode, metric)]
                fill, edge = (GATED, GATED) if mode == "gated" else (UNGATED, UNGATED_EDGE)
                out.append(f'<line x1="{x0 + panel_w * lo}" y1="{y}" x2="{x0 + panel_w * hi}" y2="{y}" stroke="{edge}" '
                           f'stroke-width="4" stroke-linecap="round"/>')
                out.append(f'<circle cx="{x0 + panel_w * rate}" cy="{y}" r="9" fill="{fill}" stroke="{PAPER}" stroke-width="2"/>')
                out.append(f'<text x="{x0 + panel_w * hi + 14 if hi < 0.6 else x0 + panel_w * lo - 14}" y="{y + 6}" font-size="17" '
                           f'fill="{INK}" text-anchor="{"start" if hi < 0.6 else "end"}">{escape(cells[(model, mode)][metric])}</text>')
                if p == 0:
                    short = re.sub(r"-\d+b-a\d+b$", "", model.split(" (")[0])  # nemotron-3-ultra, nemotron-3.5-lightning
                    out.append(f'<text x="{left - 24}" y="{y + 6}" font-size="18" fill="{INK}" text-anchor="end">'
                               f'{escape(short)}, {"with gate" if mode == "gated" else "no gate"}</text>')
                i += 1
    ly = top + row_h * 4 + 100
    out += [f'<circle cx="{left}" cy="{ly}" r="9" fill="{GATED}"/><text x="{left + 18}" y="{ly + 6}" font-size="19" fill="{INK}">With the gate</text>',
            f'<circle cx="{left + 200}" cy="{ly}" r="9" fill="{UNGATED}" stroke="{UNGATED_EDGE}" stroke-width="2"/>'
            f'<text x="{left + 218}" y="{ly + 6}" font-size="19" fill="{INK}">Without the gate</text>',
            f'<text x="60" y="{H - 90}" font-size="18" fill="{INK2}">Attempts are correlated across the 3 repeats, so these intervals overstate precision; '
            'counted per unit the gap holds (summary.md, Unit level).</text>',
            f'<text x="60" y="{H - 60}" font-size="18" fill="{INK2}">Synthetic test buildings; draft rules not reviewed by an expert; '
            'no difference between the two models may be claimed.</text>',
            f'<text x="60" y="{H - 30}" font-size="16" fill="{INK3}">Source: eval/results/{RUN}/summary.md and summary.csv (labels copied verbatim).</text>',
            "</svg>"]
    return "\n".join(out)


def pipeline() -> str:
    spec = importlib.util.spec_from_file_location("check_numbers", ROOT / "scripts" / "check_numbers.py")
    cn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cn)
    f = cn.facts(with_tests=False)
    steps = [
        ("Source text", f"{f['clauses.MBBL2016']} MBBL 2016", f"{f['clauses.TGBR2012']} Telangana 2012", "clauses"),
        ("Rule units", f"{f['units.total']} verbatim", "sentences:", f"{f['units.ids']} IDS, {f['units.geometric']} geometric"),
        ("Candidate check", "IDS 1.0 file or", "Python check, by", "hand or by an LLM"),
        ("Verifier gate", "schema, sandbox,", "pass and fail models;", "3 repairs, then a person"),
        ("Draft rulepack", f"v0: {f['rulepack.v0']} rules", "not reviewed by", "an expert yet"),
        ("Audit", "IFC4 model in,", "verdicts out: JSON,", "HTML report, BCF 2.1"),
    ]
    W, H, bw, bh, gap, y = 1600, 900, 220, 210, 32, 250
    x0 = (W - (len(steps) * bw + (len(steps) - 1) * gap)) / 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
           f'<path d="M0 0 10 5 0 10z" fill="{INK}"/></marker></defs>',
           f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
           f'<text x="60" y="90" font-size="38" fill="{INK}" font-weight="600">NIYAM: from a bye-law sentence to a checked IFC model</text>',
           f'<text x="60" y="132" font-size="22" fill="{INK2}">Every candidate rule, from a person or an LLM, must pass the gate on test models before it can be used.</text>']
    for i, (title, *lines) in enumerate(steps):
        x = x0 + i * (bw + gap)
        accent = GATED if title == "Verifier gate" else INK
        out += [f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="6" fill="#FBF8F1" stroke="{accent}" stroke-width="{3 if accent == GATED else 1.5}"/>',
                f'<text x="{x + 18}" y="{y + 40}" font-size="15" fill="{INK3}">{i + 1:02d}</text>',
                f'<text x="{x + 18}" y="{y + 76}" font-size="23" fill="{INK}" font-weight="600">{escape(title)}</text>',
                *(f'<text x="{x + 18}" y="{y + 122 + 26 * k}" font-size="16" fill="{INK2}">{escape(t)}</text>' for k, t in enumerate(lines))]
        if i:
            out.append(f'<line x1="{x - gap + 4}" y1="{y + bh / 2}" x2="{x - 6}" y2="{y + bh / 2}" stroke="{INK}" stroke-width="2" marker-end="url(#a)"/>')
    gx = x0 + 3 * (bw + gap) + bw / 2
    ey = y + bh + 150
    out += [f'<line x1="{gx}" y1="{y + bh}" x2="{gx}" y2="{ey - 60}" stroke="{GATED}" stroke-width="2" stroke-dasharray="6 6" marker-end="url(#a)"/>',
            f'<rect x="{gx - 330}" y="{ey - 56}" width="660" height="120" rx="6" fill="#FBF8F1" stroke="{GATED}" stroke-width="1.5"/>',
            f'<text x="{gx}" y="{ey - 16}" font-size="22" fill="{INK}" font-weight="600" text-anchor="middle">Evaluation, separately: held-out test buildings</text>',
            f'<text x="{gx}" y="{ey + 20}" font-size="18" fill="{INK2}" text-anchor="middle">the gate never sees them; they measure wrong_shipped</text>',
            f'<text x="{gx}" y="{ey + 46}" font-size="18" fill="{INK2}" text-anchor="middle">(run 2: {f["run.headline.calls"]} model calls, 2 open models, 3 repeats)</text>',
            f'<text x="60" y="{H - 40}" font-size="16" fill="{INK3}">Counts from rules/corpus/clause-ids.txt, docs/review/review-sheet.csv, '
            'rules/rulepack/v0/manifest.yaml and eval/results/ (scripts/check_numbers.py).</text>',
            "</svg>"]
    return "\n".join(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "07-results-chart.svg").write_text(results_chart(), encoding="utf-8")
    (OUT / "08-pipeline.svg").write_text(pipeline(), encoding="utf-8")
    labels = re.findall(r">(\d+/\d+ = [^<]+)<", (OUT / "07-results-chart.svg").read_text(encoding="utf-8"))
    assert len(labels) == 8, labels  # 2 metrics x 2 models x 2 modes, each the harness's own string
    print("wrote", OUT / "07-results-chart.svg", "and", OUT / "08-pipeline.svg")


if __name__ == "__main__":
    main()
