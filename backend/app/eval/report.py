"""summary.md and summary.csv for one evaluation run. Dry runs are bannered everywhere and never written to docs/.

Every table appears twice: over all units, and over distinct rules only (units tagged duplicate_of excluded)."""

import csv
import json
from pathlib import Path

from app.eval.metrics import distinct_only, group_metrics, paired, review_share, unit_metrics
from app.fixtures.builders import REPO_ROOT
from app.fixtures.gold_ids import load_units

RESULTS_DIR = REPO_ROOT / "eval" / "results"
DOCS_DIR = REPO_ROOT / "docs"
BANNER = "DRY RUN: synthetic responses, not model results"
COLUMNS = ["valid", "dev_correct", "heldout_correct", "shipped", "wrong_shipped", "needs_human"]
# Chosen AFTER seeing run 20261118T140452Z-5b7edb: units whose spec reading differs from the literal clause text.
POSTHOC_EXCLUDED = ("MBBL2016-4.8.2#1", "MBBL2016-5.4.1#b2")
POSTHOC_NOTE = ("excluded after seeing results because the spec reading and the literal clause text disagree; "
                "not a pre-registered analysis")


class RefusedOutput(Exception):
    pass


def _fmt(value) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def _by(items: list[dict], *keys) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    for i in items:
        groups.setdefault(tuple(i.get(k, "hand-written") for k in keys), []).append(i)
    return groups


def _tables(items: list[dict], level: str) -> list[str]:
    metrics = {k: group_metrics(v) for k, v in _by(items, "model", "mode").items()}
    lines = [f"{level} Items, correlated across repeats\n",
             "Each row of this table is one compilation; repeats of the same unit are correlated, so these intervals "
             "overstate precision when repeats > 1. The unit-level tables below count units.\n",
             "| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | "
             "mean repairs | mean tokens | mean wall s |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (model, mode), m in sorted(metrics.items()):
        cells = [str(m[c]) if m[c] is not None else "-" for c in COLUMNS]
        lines.append(f"| {model} | {mode} | {m['n']} | " + " | ".join(cells) +
                     f" | {_fmt(m['mean_repairs'])} | {_fmt(m['mean_tokens'])} | {_fmt(m['mean_wall_s'])} |")
    table = paired(items)
    if table:
        lines += [f"\n{level} Paired: gated vs ungated on the same unit and repeat (shipped and held-out correct)\n",
                  "| model | both correct | gated only | ungated only | neither |", "|---|---|---|---|---|"]
        lines += [f"| {m} | {r['both_correct']} | {r['gated_only']} | {r['ungated_only']} | {r['neither']} |"
                  for m, r in sorted(table.items())]
    for key in ("tier", "template"):
        lines += [f"\n{level} Breakdown by {key}\n",
                  f"| model | mode | {key} | n | heldout_correct | shipped | wrong_shipped |", "|---|---|---|---|---|---|---|"]
        for (model, mode, value), group in sorted(_by(items, "model", "mode", key).items()):
            m = group_metrics(group)
            lines.append(f"| {model} | {mode} | {value} | {m['n']} | {m['heldout_correct']} | {m['shipped']} | "
                         f"{m['wrong_shipped']} |")
    return lines + _unit_tables(items, level)


def posthoc_lines(items: list[dict], distinct: list[dict], level: str) -> list[str]:
    """POST-HOC sensitivity: the headline heldout_correct and wrong_shipped recomputed without POSTHOC_EXCLUDED."""
    lines = [f"{level} POST-HOC sensitivity: without {', '.join(POSTHOC_EXCLUDED)}\n",
             f"**Note: {POSTHOC_NOTE}.** The tables above are the primary results and are "
             f"unchanged; this table only shows how much these two units move the headline numbers.\n",
             "| view | model | mode | n | heldout_correct | wrong_shipped (items) | wrong_shipped per unit |",
             "|---|---|---|---|---|---|---|"]
    for view, group in (("all units", items), ("distinct rules", distinct)):
        kept = [i for i in group if i["unit_id"] not in POSTHOC_EXCLUDED]
        for (model, mode), cell in sorted(_by(kept, "model", "mode").items()):
            m = group_metrics(cell)
            lines.append(f"| {view} | {model} | {mode} | {m['n']} | {m['heldout_correct']} | {m['wrong_shipped']} | "
                         f"{unit_metrics(cell)['wrong_shipped_units']} |")
    return lines


def _unit_tables(items: list[dict], level: str) -> list[str]:
    """Unit level: per unit across repeats, stability of outcomes, and wrong_shipped with n = units."""
    cells = {k: unit_metrics(v) for k, v in sorted(_by(items, "model", "mode").items())}
    lines = [f"\n{level} Unit level: wrong_shipped per unit\n",
             "A unit counts as wrong if any repeat shipped a rule that is wrong on the held-out fixtures; n = units "
             "that shipped in at least one repeat. k/n = rate [Wilson 95% interval].\n",
             "| model | mode | units | wrong_shipped per unit |", "|---|---|---|---|"]
    lines += [f"| {model} | {mode} | {m['n_units']} | {m['wrong_shipped_units']} |" for (model, mode), m in cells.items()]
    lines += [f"\n{level} Stability across repeats\n",
              "Outcome = (shipped, held-out correct) of each repeat.\n",
              "| model | mode | units | identical in every repeat | varied |", "|---|---|---|---|---|"]
    lines += [f"| {model} | {mode} | {m['n_units']} | {m['stable']} | {m['varied']} |" for (model, mode), m in cells.items()]
    lines += [f"\n{level} Unit level: held-out-correct share per unit\n",
              "Repeats that shipped a held-out-correct rule / repeats.\n",
              "| unit | " + " | ".join(f"{model} {mode}" for model, mode in cells) + " |",
              "|---|" + "---|" * len(cells)]
    for unit in sorted({u for m in cells.values() for u in m["shares"]}):
        shares = [m["shares"].get(unit) for m in cells.values()]
        lines.append(f"| {unit} | " + " | ".join(f"{k}/{n}" if n else "-" for k, n in (s or (0, 0) for s in shares)) + " |")
    return lines


def _csv_rows(items: list[dict], view: str) -> list[list]:
    rows = []
    for (model, mode), group in sorted(_by(items, "model", "mode").items()):
        m = group_metrics(group)
        row = [view, model, mode, m["n"]]
        for c in COLUMNS:
            r = m[c]
            lo, hi = (r.wilson or (None, None)) if r else (None, None)
            row += [r.k, r.n, r.rate, lo, hi] if r else ["", "", "", "", ""]
        rows.append(row + [m["mean_repairs"], m["mean_tokens"], m["mean_wall_s"]])
    return rows


def write_report(results_path: Path, out_dir: Path | None = None) -> list[Path]:
    data = json.loads(results_path.read_text(encoding="utf-8"))
    meta, items = data["meta"], data["items"]
    out_dir = (out_dir or RESULTS_DIR / meta["run_id"]).resolve()
    if meta["dry_run"] and (out_dir == DOCS_DIR.resolve() or DOCS_DIR.resolve() in out_dir.parents):
        raise RefusedOutput(f"refusing to write a dry-run report into {DOCS_DIR}: dry-run numbers are not results")
    units = load_units()
    duplicates = {u.id: u.duplicate_of for u in units.values() if u.duplicate_of}
    distinct = distinct_only(items, duplicates)
    excluded = sorted({i["unit_id"] for i in items} & duplicates.keys())

    lines = [f"# {BANNER}\n", f"> **{BANNER}.** Never quote these numbers.\n"] if meta["dry_run"] else []
    lines += [f"# NIYAM evaluation {meta['run_id']}\n",
              f"Date {meta['date']} · commit `{meta['git_commit']}` · rulepack `{meta['rulepack_hash'][:12]}` · "
              f"temperature {meta['temperature']} · max repairs {meta['max_repairs']} · repeats {meta['repeats']} · "
              f"providers {meta['provider_classes']} · dry_run={str(meta['dry_run']).lower()}\n"]
    for name, why in meta.get("skipped_models", {}).items():
        lines.append(f"**Skipped model:** {name}: {why}\n")
    if meta.get("stopped_early"):
        lines.append(f"**Stopped early:** {meta['stopped_early']}\n")
    n_max = max((len(g) for g in _by(items, "model", "mode").values()), default=0)
    if n_max < 30:
        lines.append(f"Each cell has n ≤ {n_max} (n < 30): the 95% intervals are wide; differences between rows are "
                     "not evidence of a real difference.\n")
    lines += ["Rates are k/n = rate [Wilson 95% interval]. wrong_shipped is over shipped rules: how often a rule that "
              "is wrong on the held-out fixtures reaches the rulepack.\n", "## All units\n"]
    lines += _tables(items, "###")
    lines.append("\n## Distinct rules only\n")
    lines.append(("Excluded from the distinct view: " + ", ".join(f"{u} (duplicate of {duplicates[u]})" for u in excluded)
                  + ". They encode the same requirement as another unit, so counting both would weight it twice.\n")
                 if excluded else "No unit in this run is tagged as a duplicate; the distinct view equals the full one.\n")
    lines += _tables(distinct, "###")
    lines += ["", *posthoc_lines(items, distinct, "##")]
    share = review_share(units.values())
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
        w.writerow(["view", "model", "mode", "n", *(f"{c}_{x}" for c in COLUMNS for x in ("k", "n", "rate", "lo", "hi")),
                    "mean_repairs", "mean_tokens", "mean_wall_s"])
        w.writerows(_csv_rows(items, "all_units") + _csv_rows(distinct, "distinct_rules"))
    return [md, path_csv]
