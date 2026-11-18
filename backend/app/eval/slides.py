"""slides-data.md and slides-data.csv for one REAL evaluation run: the numbers a slide may show, with their n and
Wilson intervals. Dry runs and runs from uncommitted code are refused."""

import csv
import json
from pathlib import Path

from app.eval.metrics import distinct_only, group_metrics
from app.eval.report import COLUMNS, RESULTS_DIR, RefusedOutput, _by, _tables
from app.fixtures.gold_ids import load_units

CAUTION = ("Caution: n is small (one repeat per unit), so every interval is wide; no model difference may be claimed, "
           "and no mode difference beyond what the intervals show.")


def _csv_rows(run_id: str, view: str, items: list[dict]) -> list[list]:
    rows = []
    for group_key in ("cell", "tier", "template"):
        keys = ("model", "mode") if group_key == "cell" else ("model", "mode", group_key)
        for key, group in sorted(_by(items, *keys).items()):
            m = group_metrics(group)
            for metric in COLUMNS:
                r = m[metric]
                if r is None:
                    continue
                lo, hi = r.wilson or ("", "")
                rows.append([run_id, view, key[0], key[1], group_key, key[2] if len(key) > 2 else "", metric,
                             r.k, r.n, "" if r.rate is None else r.rate, lo, hi])
    return rows


def write_slides(results_path: Path, out_dir: Path | None = None) -> list[Path]:
    data = json.loads(results_path.read_text(encoding="utf-8"))
    meta, items = data["meta"], data["items"]
    if meta["dry_run"]:
        raise RefusedOutput("refusing slide data for a dry run: dry-run numbers are not results")
    if meta["git_commit"].endswith("-dirty") or meta["git_commit"] == "unknown":
        raise RefusedOutput(f"refusing slide data for commit {meta['git_commit']!r}: rerun from a clean, committed tree")
    duplicates = {u.id: u.duplicate_of for u in load_units().values() if u.duplicate_of}
    distinct = distinct_only(items, duplicates)
    fallback = sum(i.get("answered_model", i["model"]) != i["model"] for i in items)

    lines = [f"# NIYAM slide data: run {meta['run_id']}\n",
             f"- Date: {meta['date']}", f"- Commit: `{meta['git_commit']}`",
             f"- Rulepack hash: `{meta['rulepack_hash']}`",
             "- Models: " + "; ".join(f"{m['name']} ({m['role']})" for m in meta["models"]),
             f"- Provider classes: {meta['provider_classes']}; request extras: {meta.get('request_extras', {})}",
             f"- Temperature {meta['temperature']}, max repairs {meta['max_repairs']}, repeats {meta['repeats']}, "
             f"dry_run=false",
             f"- Calls used: {meta['used']['calls']}, tokens used: {meta['used']['tokens']}",
             f"- Stopped early: {meta['stopped_early'] or 'no'}",
             "- Skipped models: " + ("; ".join(f"{k} ({v})" for k, v in meta.get("skipped_models", {}).items()) or "none"),
             f"- Fallback items: {fallback} (only on_limit=wait is implemented; each item was answered by its model)",
             "", f"**{CAUTION}**", "",
             "## Headline: wrong_shipped, gated vs ungated\n",
             "wrong_shipped = shipped rules that are wrong on the held-out fixtures / shipped rules, "
             "as k/n = rate [Wilson 95% interval].\n",
             "| view | model | gated | ungated |", "|---|---|---|---|"]
    for view, group in (("all units", items), ("distinct rules", distinct)):
        cells = {k: group_metrics(v)["wrong_shipped"] for k, v in _by(group, "model", "mode").items()}
        for model in sorted({m for m, _ in cells}):
            lines.append(f"| {view} | {model} | {cells.get((model, 'gated'), '-')} | {cells.get((model, 'ungated'), '-')} |")
    lines += ["", "## All units\n", *_tables(items, "###"), "", "## Distinct rules only\n",
              "Excluded as duplicates: " + (", ".join(sorted({i["unit_id"] for i in items} & duplicates.keys()))
                                            or "none") + "\n", *_tables(distinct, "###"), "", CAUTION]

    out_dir = out_dir or RESULTS_DIR / meta["run_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    md, path_csv = out_dir / "slides-data.md", out_dir / "slides-data.csv"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(path_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["run_id", "view", "model", "mode", "group", "group_value", "metric", "k", "n", "rate",
                    "wilson_lo", "wilson_hi"])
        w.writerows(_csv_rows(meta["run_id"], "all_units", items) + _csv_rows(meta["run_id"], "distinct_rules", distinct))
    return [md, path_csv]
