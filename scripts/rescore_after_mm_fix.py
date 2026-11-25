"""Re-score (not re-run) the stored final candidates of committed evaluation runs on the current fixtures and helpers.
Offline: no model is called. The generate-verify-repair loop is not replayed: with the gate's corrected pass/fail
models a live run could repair differently and ship different code, so this answers "how do the shipped candidates
score after the unit fix", not "what would the corrected run produce". Writes only under eval/results/rescore-after-mm-fix/; committed results are never touched.

The committed results.json files hold scores, not candidates. The candidates live in the local, gitignored attempt
logs (eval/runs/<run_id>/attempts/...), the same `attempts[-1].extracted_xml` the runner scored. Geometric items
only: IDS candidates are scored on door fixtures, which the millimetre fix does not change.

Run from backend/ with the venv active, once before and once after the fix:
    python ../scripts/rescore_after_mm_fix.py score before
    python ../scripts/rescore_after_mm_fix.py score after
    python ../scripts/rescore_after_mm_fix.py compare
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.eval.runner import RUNS_DIR  # noqa: E402
from app.eval.scoring import score_candidate  # noqa: E402
from app.fixtures.builders import REPO_ROOT, safe_name  # noqa: E402
from app.fixtures.gold_ids import load_units  # noqa: E402

RUNS = ["20261118T140452Z-5b7edb", "20261118T180916Z-4b9c93"]  # run 2 and the Telangana case study
OUT = REPO_ROOT / "eval" / "results" / "rescore-after-mm-fix"
KEYS = ("valid", "dev_correct", "heldout_correct", "vacuous")


def _attempts(run_id: str) -> dict[tuple, Path]:
    found = {}
    for p in (RUNS_DIR / run_id / "attempts").rglob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        model_dir, mode, repeat = p.parts[-4], p.parts[-3], int(p.parts[-2].removeprefix("repeat"))
        found[(model_dir, mode, repeat, d["unit_id"])] = p
    return found


def score(phase: str) -> None:
    units = load_units()
    out = {"phase": phase, "runs": {}}
    for run_id in RUNS:
        committed = json.loads((REPO_ROOT / "eval" / "results" / run_id / "results.json").read_text(encoding="utf-8"))
        attempts = _attempts(run_id)
        rows = []
        for item in committed["items"]:
            if item["tier"] != "geometric":
                continue
            key = (safe_name(item["model"]), item["mode"], int(item["repeat"]), item["unit_id"])
            path = attempts.get(key)
            row = {"model": item["model"], "mode": item["mode"], "repeat": int(item["repeat"]),
                   "unit_id": item["unit_id"], "shipped": str(item["shipped"]) == "True",
                   "committed": {k: item["score"][k] for k in KEYS}}
            if path is None:
                row["error"] = "attempt log not found"
            else:
                log = json.loads(path.read_text(encoding="utf-8"))
                final = log["attempts"][-1]["extracted_xml"] if log["attempts"] else None
                s = score_candidate(units[item["unit_id"]], final).to_dict()
                row["rescored"] = {k: s[k] for k in KEYS}
                row["rescore_error"] = s["error"]
                row["heldout_mismatches"] = s["heldout_mismatches"]
            rows.append(row)
            print(f"{run_id} {item['model'][:24]:24} {item['mode']:8} r{item['repeat']} {item['unit_id']:24} "
                  f"{row.get('rescored', row.get('error'))}", flush=True)
        out["runs"][run_id] = rows
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{phase}.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


def compare() -> None:
    before = json.loads((OUT / "before.json").read_text(encoding="utf-8"))
    after = json.loads((OUT / "after.json").read_text(encoding="utf-8"))
    for run_id in RUNS:  # the comparison only means something if "before" reproduces the committed scores
        bad = [r for r in before["runs"][run_id] if r.get("rescored") != r["committed"]]
        if bad:
            for r in bad:
                print("NOT REPRODUCED", run_id, r["model"], r["mode"], r["repeat"], r["unit_id"], r["committed"],
                      r.get("rescored"), r.get("rescore_error") or r.get("error"))
            raise SystemExit(f"{run_id}: {len(bad)} item(s) not reproduced before the fix; no comparison written")
    lines = ["# Re-scored after the unit fix (a re-score, not a re-run)", "",
             "Offline: the final candidate of each geometric item, read from the local attempt logs, scored again with",
             "`app.eval.scoring.score_candidate`. **before** = the code and fixtures at the start of branch fix-mm-units",
             "(reproduces the committed scores); **after** = helpers without the extra scale and regenerated",
             "millimetre fixtures. The committed results under eval/results/<run>/ are unchanged.", "",
             "This does not replay the generate-verify-repair loop. The gate's pass and fail models changed, so a live",
             "run could repair differently and ship different code: these numbers are \"re-scored after the unit fix\",",
             "not a corrected headline run.", ""]
    for run_id in RUNS:
        b_rows, a_rows = before["runs"][run_id], after["runs"][run_id]
        reproduced = sum(r.get("rescored") == r["committed"] for r in b_rows)
        changes = []
        for b, a in zip(b_rows, a_rows):
            assert (b["model"], b["mode"], b["repeat"], b["unit_id"]) == (a["model"], a["mode"], a["repeat"], a["unit_id"])
            if a.get("rescored") != b.get("rescored"):
                changes.append((b, a))
        lines += [f"## {run_id}", "",
                  f"- geometric items: {len(b_rows)}",
                  f"- before-fix re-score equals the committed score: {reproduced} of {len(b_rows)}",
                  f"- items whose score changes after the fix: {len(changes)}", ""]
        for key in KEYS:
            ups = sum(not b["rescored"][key] and a["rescored"][key] for b, a in changes)
            downs = sum(b["rescored"][key] and not a["rescored"][key] for b, a in changes)
            lines.append(f"- `{key}`: {ups} false -> true, {downs} true -> false")
        shipped_wrong = lambda rows: sum(r["shipped"] and not r["rescored"]["heldout_correct"] for r in rows)
        lines += ["", f"- shipped and held-out wrong: {shipped_wrong(b_rows)} before, {shipped_wrong(a_rows)} after "
                  f"(of {sum(r['shipped'] for r in b_rows)} shipped geometric items)", ""]
        if changes:
            lines += ["| model | mode | repeat | unit | shipped | before (valid/dev/heldout/vacuous) | after |",
                      "|---|---|---|---|---|---|---|"]
            fmt = lambda s: "/".join("T" if s[k] else "F" for k in KEYS)
            for b, a in changes:
                lines.append(f"| {b['model']} | {b['mode']} | {b['repeat']} | {b['unit_id']} | {b['shipped']} | "
                             f"{fmt(b['rescored'])} | {fmt(a['rescored'])} |")
            lines.append("")
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1:2] == ["score"]:
        score(sys.argv[2])
    elif sys.argv[1:2] == ["compare"]:
        compare()
    else:
        raise SystemExit(__doc__)
