"""Every number a reader sees must equal a committed result. Checks README.md, STATUS.md, docs/**/*.md, submission/**/*.md,
the evaluation reports, the landing page content file and the generated landing data against committed files:
eval/results/*/results.json, summary.csv, the re-score after.json, docs/review/review-sheet.csv, rules/corpus/clause-ids.txt,
rules/rulepack/v0/manifest.yaml, the fixture folders and git history.

Two kinds of check:
- rate strings "k/n = r% [lo%, hi%]" anywhere must be written exactly as the harness wrote them in a committed summary.md;
- counted claims ("445 clauses", "415 model calls", "6 rules" for v0, "21 of 199 shipped geometric", ...) must equal the
  fact computed from the committed files. The fact a number belongs to is taken from the nearest keyword before it on the
  same line (e.g. "Telangana" or "run 2").

Usage (repository root):  python scripts/check_numbers.py [--tests]
--tests also collects the backend (pytest) and frontend (vitest) tests and checks every quoted test count.
Exit 1 on any mismatch."""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = {"pilot": "20261118T133025Z-4c4519", "headline": "20261118T140452Z-5b7edb", "telangana": "20261118T180916Z-4b9c93"}
RATE = re.compile(r"\b\d+/\d+ = \d+% \[\d+%, \d+%\]")
# not reader text: clause quotations, the keyword-scored candidate list and dry runs
SKIP = {"docs/review/review-sheet.md", "docs/corpus-candidates.md"}


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def facts(with_tests: bool) -> dict[str, int]:
    f: dict[str, int] = {}
    ids = [l for l in read("rules/corpus/clause-ids.txt").splitlines() if l and not l.startswith("#")]
    for src in ("MBBL2016", "TGBR2012"):
        f[f"clauses.{src}"] = sum(i.startswith(src + "-") for i in ids)
    f["clauses.total"] = len(ids)
    tg = [i for i in ids if i.startswith("TGBR2012-")]
    f["clauses.TGBR2012.rules"] = sum(i.split("-", 1)[1].isdigit() for i in tg)
    f["clauses.TGBR2012.annexures"] = sum("Annexure" in i for i in tg)
    f["clauses.TGBR2012.appendices"] = sum("Appendix" in i for i in tg)

    with open(ROOT / "docs/review/review-sheet.csv", encoding="utf-8-sig", newline="") as fh:
        units = list(csv.DictReader(fh))
    specs = {p.stem for p in (ROOT / "rules/specs").glob("*.yaml")}
    mbbl = [u for u in units if u["unit_id"].startswith("MBBL2016")]
    f["units.total"] = len(units)
    f["units.MBBL2016"] = len(mbbl)
    f["units.TGBR2012"] = len(units) - len(mbbl)
    f["units.duplicates"] = sum(bool(u["duplicate_of"]) for u in units)
    f["units.distinct.MBBL2016"] = f["units.MBBL2016"] - f["units.duplicates"]
    f["units.distinct"] = f["units.total"] - f["units.duplicates"]
    f["units.ids"] = sum(u["tier"] == "ids" for u in units)
    f["units.geometric"] = sum(u["tier"] == "geometric" for u in units)
    f["units.geometric.MBBL2016"] = sum(u["tier"] == "geometric" for u in mbbl)
    f["units.hand_written"] = sum(re.sub(r"[.#]", "_", u["unit_id"]) not in specs for u in units)
    f["units.from_specs.MBBL2016"] = f["units.MBBL2016"] - f["units.hand_written"]
    f["units.reading_dependent"] = sum(bool(u.get("reading_dependent")) for u in units)

    manifest = read("rules/rulepack/v0/manifest.yaml")
    f["rulepack.v0"] = len(re.findall(r"^- unit_id:", manifest, re.M))
    f["rulepack.v0.ids"] = len(re.findall(r"^  tier: ids$", manifest, re.M))
    f["rulepack.v0.geometric"] = len(re.findall(r"^  tier: geometric$", manifest, re.M))

    for name, run in RUNS.items():
        meta = json.loads(read(f"eval/results/{run}/results.json"))["meta"]
        f[f"run.{name}.calls"] = meta["used"]["calls"]
        f[f"run.{name}.tokens"] = meta["used"]["tokens"]
        f[f"run.{name}.models"] = len(meta["models"])
        f[f"run.{name}.repeats"] = meta["repeats"]
    f["run.models"] = f["run.headline.models"]

    after = json.loads(read("eval/results/rescore-after-mm-fix/after.json"))["runs"]
    f["rescore.changed"] = 0
    for name in ("headline", "telangana"):
        rows = after[RUNS[name]]
        shipped = [r for r in rows if r["shipped"]]
        f[f"rescore.{name}.items"] = len(rows)
        f[f"rescore.{name}.shipped"] = len(shipped)
        f[f"rescore.{name}.wrong"] = sum(not r["rescored"]["heldout_correct"] for r in shipped)
        f["rescore.changed"] += sum(r["committed"] != r["rescored"] for r in rows)
    f["rescore.items"] = f["rescore.headline.items"] + f["rescore.telangana.items"]

    count = lambda d, pat: len(list((ROOT / d).glob(pat)))
    f["fixtures.dev"] = count("fixtures/ifc", "*.ifc")
    f["fixtures.heldout"] = count("fixtures/heldout", "*.ifc")
    f["fixtures.samples"] = count("fixtures/samples", "*.ifc")
    f["fixtures.real"] = len(list((ROOT / "fixtures/real").rglob("*.ifc")))
    fix = subprocess.run(["git", "log", "--format=%H", "--grep", "Fix the millimetre double scale"], cwd=ROOT,
                         capture_output=True, text=True).stdout.split()
    if fix:
        changed = subprocess.run(["git", "show", "--name-only", "--format=", fix[-1], "--", "*.ifc"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.split()
        f["fixtures.regenerated_mm"] = len([c for c in changed if not c.startswith("fixtures/invalid/")])

    if with_tests:
        py = ROOT / "backend" / (".venv/Scripts/python.exe" if sys.platform == "win32" else ".venv/bin/python")
        out = subprocess.run([str(py), "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=ROOT / "backend",
                             capture_output=True, text=True).stdout
        f["tests.backend"] = int(re.search(r"(\d+) tests? collected", out).group(1))
        # a run, not `vitest list`: list misses tests that a run counts (41 run vs 37 listed on 25 November 2026)
        report = ROOT / "frontend" / "test-results" / "vitest-count.json"
        subprocess.run(f'npx vitest run --reporter=json --outputFile="{report}"', cwd=ROOT / "frontend",
                       capture_output=True, text=True, shell=True)
        f["tests.frontend"] = json.loads(report.read_text(encoding="utf-8"))["numTotalTests"]
    return f


# (regex whose group 1 is the number, {keyword before it on the line: fact}, fact when no keyword or None = any)
RUN_CTX = {r"run 1|pilot|4c4519": "pilot", r"run 2|headline|5b7edb": "headline", r"Telangana|TGBR|4b9c93": "telangana"}
CLAIMS: list[tuple[str, dict[str, str], str | None]] = [
    # at most 3 digits: in "MBBL 2016 clauses" the number is a year, not a count
    (r"(?<!to )\b(\d{1,3}) clauses\b", {r"MBBL": "clauses.MBBL2016", r"Telangana|TGBR": "clauses.TGBR2012"}, "clauses.total"),
    (r"\b(\d+) clauses read", {}, "clauses.total"),
    (r"\((\d+) rules, \d+ annexures", {}, "clauses.TGBR2012.rules"),
    (r"\b(\d+) annexures", {}, "clauses.TGBR2012.annexures"),
    (r"\b(\d+) appendices", {}, "clauses.TGBR2012.appendices"),
    (r"\b(\d+) (?:verbatim |draft )?(?:rule )?units?\b(?=:| \(|,| in all| total)", {r"MBBL": "units.MBBL2016", r"Telangana|TGBR": "units.TGBR2012"}, "units.total"),
    (r"\b(\d+) MBBL(?: 2016)? units", {}, "units.MBBL2016"),
    (r"\b(\d+) Telangana units", {}, "units.TGBR2012"),
    (r"units: (\d+) MBBL", {}, "units.MBBL2016"),
    (r"\((\d+) distinct\)", {}, "units.distinct.MBBL2016"),
    (r"\b(\d+) distinct in all", {}, "units.distinct"),
    (r"\b(\d+) tagged as duplicates|\b(\d+) duplicates?\b", {}, "units.duplicates"),
    (r"\b(\d+) hand-written pilots", {}, "units.hand_written"),
    (r"\b(\d+) from rule specs", {r"Telangana": "units.TGBR2012"}, "units.from_specs.MBBL2016"),
    (r"\b(\d+) IDS, \d+ geometric", {}, "units.ids"),
    (r"\b\d+ IDS, (\d+) geometric", {}, "units.geometric.MBBL2016"),
    (r"\b(\d+) reading-dependent", {}, "units.reading_dependent"),
    (r"[Rr]ulepack v0(?::| \()\s*(\d+)", {}, "rulepack.v0"),
    (r"\bv0 \((\d+)", {}, "rulepack.v0"),
    (r"\((\d+) door IDS", {}, "rulepack.v0.ids"),
    (r"\b(\d[\d,]*) (?:model |LLM )?calls\b", RUN_CTX, None),
    (r"\b(\d{1,3}(?:,\d{3})+|\d{5,}) tokens\b", RUN_CTX, None),
    (r"\b(\d+) of \d+ (?:geometric|re-scored|stored)[^\n]{0,20}?(?:outcomes|items)? changed", {}, "rescore.changed"),
    (r"\b\d+ of (\d+) geometric outcomes", {}, "rescore.items"),
    (r"\b(\d+) of \d+ shipped geometric", {r"Telangana|TGBR|4b9c93": "rescore.telangana.wrong", r"run 2|5b7edb": "rescore.headline.wrong"}, None),
    (r"\b\d+ of (\d+) shipped geometric", {r"Telangana|TGBR|4b9c93": "rescore.telangana.shipped", r"run 2|5b7edb": "rescore.headline.shipped"}, None),
    (r"\b(\d+) millimetre fixtures", {}, "fixtures.regenerated_mm"),
    (r"\b(\d+) dev fixtures", {}, "fixtures.dev"),
    (r"\b(\d+) held-out fixtures", {}, "fixtures.heldout"),
    (r"\b(\d+) (?:synthetic )?sample (?:buildings|models|files)", {}, "fixtures.samples"),
    (r"\b(\d+) (?:backend|pytest) tests|pytest:? (\d+) passed|\b(\d+) passed \(pytest", {}, "tests.backend"),
    (r"\b(\d+) (?:frontend|vitest) tests|vitest:? (\d+) passed|\b(\d+) passed \(vitest", {}, "tests.frontend"),
]


def reader_files() -> list[str]:
    files = ["README.md", "STATUS.md", "eval/results/rescore-after-mm-fix/README.md", "frontend/src/content/site.ts"]
    files += [p.relative_to(ROOT).as_posix() for d in ("docs", "submission") if (ROOT / d).exists() for p in sorted((ROOT / d).rglob("*.md"))]
    files += [f"eval/results/{r}/{n}" for r in RUNS.values() for n in ("summary.md", "slides-data.md")]
    return [f for f in files if f not in SKIP and (ROOT / f).exists()]


def committed_rates() -> set[str]:
    return {m for r in RUNS.values() for n in ("summary.md", "slides-data.md") for m in RATE.findall(read(f"eval/results/{r}/{n}"))}


def check(f: dict[str, int]) -> tuple[list[str], int]:
    bad, checked, rates = [], 0, committed_rates()
    for rel in reader_files():
        b, c = check_text(rel, read(rel), f, rates)
        bad += b
        checked += c
    site = json.loads(read("frontend/src/data/site-data.json"))
    for path, key in [(("corpus", "MBBL2016"), "clauses.MBBL2016"), (("corpus", "TGBR2012"), "clauses.TGBR2012"),
                      (("units", "total"), "units.total"), (("units", "distinct"), "units.distinct"),
                      (("headline", "provenance", "calls"), "run.headline.calls"), (("pilot", "provenance", "calls"), "run.pilot.calls"),
                      (("telangana", "provenance", "calls"), "run.telangana.calls"), (("telangana", "unitsInRun"), "units.TGBR2012")]:
        v = site
        for p in path:
            v = v[p]
        checked += 1
        if v != f[key]:
            bad.append(f"frontend/src/data/site-data.json: {'.'.join(path)} = {v}, should be {f[key]} ({key})")
    return bad, checked


def check_text(rel: str, text: str, f: dict[str, int], rates: set[str]) -> tuple[list[str], int]:
    bad, checked = [], 0
    for no, line in enumerate(text.splitlines(), 1):
            for s in RATE.findall(line):
                checked += 1
                if s not in rates:
                    bad.append(f"{rel}:{no}: rate '{s}' is not in any committed summary.md")
            for pattern, ctx, default in CLAIMS:
                for m in re.finditer(pattern, line):
                    raw = next(g for g in m.groups() if g is not None)
                    value = int(raw.replace(",", ""))
                    before = line[: m.start()]
                    # a keyword right after the number, before any punctuation ("445 clauses from MBBL") wins
                    ahead = [(mm.start(1), fact) for kw, fact in ctx.items()
                             if (mm := re.match(rf"[^;:.,()]{{0,30}}?({kw})", line[m.end():]))]
                    hits = [(mm.end(), fact) for kw, fact in ctx.items() for mm in re.finditer(kw, before)]
                    key = min(ahead)[1] if ahead else max(hits)[1] if hits else default
                    if key in RUN_CTX.values():
                        key = f"run.{key}.{'calls' if 'calls' in pattern else 'tokens'}"
                    if key is None:  # no context: the number must be one of this claim's facts
                        allowed = {f[k] for k in (f"run.{r}.{'calls' if 'calls' in pattern else 'tokens'}" for r in RUNS) if k in f} \
                            if ctx is RUN_CTX else {f[v] for v in ctx.values() if v in f}
                        checked += 1
                        if value not in allowed:
                            bad.append(f"{rel}:{no}: '{m.group(0)}' matches none of {sorted(allowed)}")
                        continue
                    if key not in f:
                        continue  # e.g. test counts without --tests
                    checked += 1
                    if value != f[key]:
                        bad.append(f"{rel}:{no}: '{m.group(0)}' should be {f[key]} ({key})")
    return bad, checked


def main() -> int:
    f = facts("--tests" in sys.argv)
    bad, checked = check(f)
    for b in bad:
        print("MISMATCH", b)
    print(f"check_numbers: {checked} numbers checked in {len(reader_files())} files, {len(bad)} mismatch(es)")
    if "--facts" in sys.argv:
        print(json.dumps(f, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
