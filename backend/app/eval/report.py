"""summary.md and summary.csv for one evaluation run. Dry runs are bannered everywhere and never written to docs/."""

import csv
import json
from pathlib import Path

from app.eval.metrics import group_metrics, paired, review_share
from app.fixtures.builders import REPO_ROOT
from app.fixtures.gold_ids import load_units

RESULTS_DIR = REPO_ROOT / "eval" / "results"
DOCS_DIR = REPO_ROOT / "docs"
BANNER = "DRY RUN: synthetic responses, not model results"
COLUMNS = ["valid", "dev_correct", "heldout_correct", "shipped", "wrong_shipped", "needs_human"]


class RefusedOutput(Exception):
    pass


def _fmt(value) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def write_report(results_path: Path, out_dir: Path | None = None) -> list[Path]:
    data = json.loads(results_path.read_text(encoding="utf-8"))
    meta, items = data["meta"], data["items"]
    out_dir = (out_dir or RESULTS_DIR / meta["run_id"]).resolve()
    if meta["dry_run"] and (out_dir == DOCS_DIR.resolve() or DOCS_DIR.resolve() in out_dir.parents):
        raise RefusedOutput(f"refusing to write a dry-run report into {DOCS_DIR}: dry-run numbers are not results")
    groups: dict[tuple[str, str], list[dict]] = {}
    for i in items:
        groups.setdefault((i["model"], i["mode"]), []).append(i)
    metrics = {k: group_metrics(v) for k, v in groups.items()}

    lines = [f"# {BANNER}\n", f"> **{BANNER}.** Never quote these numbers.\n"] if meta["dry_run"] else []
    lines += [f"# NIYAM evaluation {meta['run_id']}\n",
              f"Date {meta['date']} · commit `{meta['git_commit']}` · rulepack `{meta['rulepack_hash'][:12]}` · "
              f"temperature {meta['temperature']} · max repairs {meta['max_repairs']} · repeats {meta['repeats']} · "
              f"providers {meta['provider_classes']} · dry_run={str(meta['dry_run']).lower()}\n"]
    if meta.get("stopped_early"):
        lines.append(f"**Stopped early:** {meta['stopped_early']}\n")
    n_max = max((m["n"] for m in metrics.values()), default=0)
    if n_max < 30:
        lines.append(f"Each cell has n ≤ {n_max} (n < 30): the 95% intervals are wide; differences between rows are "
                     "not evidence of a real difference.\n")
    lines += ["Rates are k/n = rate [Wilson 95% interval]. wrong_shipped is over shipped rules: how often a rule that "
              "is wrong on the held-out fixtures reaches the rulepack.\n",
              "| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | "
              "mean repairs | mean tokens | mean wall s |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (model, mode), m in sorted(metrics.items()):
        cells = [str(m[c]) if m[c] is not None else "-" for c in COLUMNS]
        lines.append(f"| {model} | {mode} | {m['n']} | " + " | ".join(cells) +
                     f" | {_fmt(m['mean_repairs'])} | {_fmt(m['mean_tokens'])} | {_fmt(m['mean_wall_s'])} |")
    table = paired(items)
    if table:
        lines += ["\n## Paired: gated vs ungated on the same unit and repeat (shipped and held-out correct)\n",
                  "| model | both correct | gated only | ungated only | neither |", "|---|---|---|---|---|"]
        lines += [f"| {m} | {r['both_correct']} | {r['gated_only']} | {r['ungated_only']} | {r['neither']} |"
                  for m, r in sorted(table.items())]
    for key, title in (("tier", "tier"), ("template", "template")):
        by: dict[tuple, list[dict]] = {}
        for i in items:
            by.setdefault((i["model"], i["mode"], i.get(key, "hand-written")), []).append(i)
        lines += [f"\n## Breakdown by {title}\n",
                  f"| model | mode | {title} | n | heldout_correct | shipped | wrong_shipped |",
                  "|---|---|---|---|---|---|---|"]
        for (model, mode, value), group in sorted(by.items()):
            m = group_metrics(group)
            lines.append(f"| {model} | {mode} | {value} | {m['n']} | {m['heldout_correct']} | {m['shipped']} | "
                         f"{m['wrong_shipped']} |")
    share = review_share(load_units().values())
    lines.append("\n## Human review\n")
    lines.append(f"Reviewed rules with decision modify or reject: {share}" if share else
                 "No reviewer decisions recorded yet (docs/review/review-sheet.csv).")

    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / "summary.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path_csv = out_dir / "summary.csv"
    with open(path_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if meta["dry_run"]:
            w.writerow([BANNER])
        w.writerow(["model", "mode", "n", *(f"{c}_{x}" for c in COLUMNS for x in ("k", "n", "rate", "lo", "hi")),
                    "mean_repairs", "mean_tokens", "mean_wall_s"])
        for (model, mode), m in sorted(metrics.items()):
            row = [model, mode, m["n"]]
            for c in COLUMNS:
                r = m[c]
                lo, hi = (r.wilson or (None, None)) if r else (None, None)
                row += [r.k, r.n, r.rate, lo, hi] if r else ["", "", "", "", ""]
            w.writerow(row + [m["mean_repairs"], m["mean_tokens"], m["mean_wall_s"]])
    return [md, path_csv]
