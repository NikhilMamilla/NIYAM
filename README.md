# NIYAM

NIYAM turns sentences from Indian building bye-laws (the MoHUA Model Building Bye-Laws 2016, and as a second
source the Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied)) into
machine checks: buildingSMART [IDS 1.0](https://github.com/buildingSMART/IDS) files for declared data and small
sandboxed Python checks for values computed from geometry. Every candidate rule, whether written by a person or
an LLM, must pass a verifier gate on test models before it can be used. It then audits IFC building models, shows
the results beside the model in 3D, and exports HTML reports and BCF issues.

**Status: research prototype.** Every rule is a draft that no domain expert has reviewed yet, and all test
buildings are synthetic.

## What NIYAM is, and is not

<!-- site-data: statements. The landing page shows these bullets verbatim (npm run site-data); keep them plain text. -->
- **Decision aid.** NIYAM is a decision aid, not a legal approval tool: a result is a lead for a person to check, never a building approval.
- **A person decides what ships.** Rules are drafted from public bye-laws (MBBL 2016 and the Telangana Building Rules 2012 base text, amendments not applied), and a person approves what enters the rulepack. No domain expert has reviewed any rule yet.
- **Four verdicts.** Every element gets passed, failed, unchecked or out_of_scope. Missing data gives unchecked, never passed.
- **Headline metric: wrong_shipped.** wrong_shipped is the share of shipped rules that are wrong on held-out test buildings the gate never sees. In run 2, with the gate: 2/68 = 3% [1%, 10%] (nemotron-3-ultra) and 0/50 = 0% [0%, 7%] (nemotron-3.5-lightning); without it: 20/75 = 27% [18%, 38%] and 31/75 = 41% [31%, 53%]. Each figure is k/n = rate [Wilson 95% interval], counted over attempts, which are correlated across 3 repeats.
- **Re-scored after the millimetre fix.** Run 2 and the Telangana run were re-scored after the millimetre fix, and 0 of 240 geometric outcomes changed. This is a re-score of the stored candidates, not a re-run.
- **Where the fix was tested.** The millimetre fix was verified on a hand-written IFC file and on one SketchUp-exported file, not on Revit or ArchiCAD exports.
- **Real models lack the data.** On the two real buildingSMART models most rules return unchecked or find nothing to check, because the data they need (for example Pset_SpaceCommon.Category on rooms) is missing.
- **Post hoc, labelled.** The two reading-dependent units (MBBL2016-4.8.2#1, MBBL2016-5.4.1#b2) were flagged after seeing the results, and the sensitivity table without them is post hoc, not pre-registered.
- **Telangana is a case study.** Only 2 Telangana units were turned into rules, from 55 ingested clauses, so Telangana is reported as a case study with counts, not as a headline rate.
<!-- /site-data: statements -->

## Pipeline

| Step | What happens |
|---|---|
| 1. Source text | The MBBL 2016 PDF becomes a corpus of 445 clauses; the Telangana Building Rules 2012 PDF becomes 55 clauses. |
| 2. Rule units | Single sentences are lifted out verbatim as rule units (25 from MBBL, 2 from Telangana; see Coverage below). |
| 3. Candidate check | Each unit becomes a candidate IDS file or Python check, written either by hand (a rule spec) or by the LLM compiler, with or without the gate. |
| 4. Verifier gate | The candidate runs on development fixtures: it must pass the schema and sandbox checks, accept the model that should pass and reject the model that should fail. |
| 5. Draft rulepack | Accepted candidates form the draft rulepack and an exported review sheet. No rule has been reviewed by a domain expert yet. |
| 6. Audit | An IFC model goes through the audit engine, which produces JSON, an HTML report, BCF issues and the web app with its 3D view. |
| 7. Evaluation | Separately, compilation is scored per model and mode on held-out fixtures that the gate never sees. |

## Status

| Area | State |
|---|---|
| Corpus: MBBL 2016, 445 clauses, search and curation CLI | works |
| Corpus: Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied), 55 clauses (29 rules, 12 annexures, 14 appendices) | ingested; **not reviewed**; coarse segmentation (rule level, annexures whole) |
| Rule units: 27 verbatim units: 25 MBBL 2016 (6 hand-written pilots, 19 from rule specs; 3 tagged as duplicates; 7 IDS, 18 geometric) and 2 Telangana (from rule specs, both geometric) | works; **drafts, not human-reviewed**; each is a single-element threshold, conditions in the clause are not encoded |
| IDS gate and sandboxed geometric gate | works (the sandbox is defence in depth, not a hard security boundary) |
| LLM compiler, both tiers, with gated repair loop | works; real runs with two NVIDIA models in `eval/results/`: pilot run 1 `20261118T133025Z-4c4519` and headline run 2 `20261118T140452Z-5b7edb` on the 25 MBBL units, and a Telangana case study `20261118T180916Z-4b9c93` on its 2 units (counts only, no rates) |
| Rulepack v0: 6 rules (3 door IDS, 3 room/stair Python) | works; **drafts, not reviewed** |
| Audit engine, HTML and BCF export, upload API, web app with 3D viewer | works on synthetic IFC4 models |
| Evaluation harness: held-out scoring, Wilson intervals, dry run, live-run preflight | works; dry-run numbers are synthetic and must never be quoted |
| Review sheet for domain experts | exported; **no decisions returned yet** |
| Real-building checks (two real IFC4 exports tried: `docs/real-models.md`), more rule templates | audit runs on them but finds almost nothing it can check |
| Data-readiness IDS (`docs/readiness/niyam-data-readiness.ids`) | generated from the rules; tells a modeller what data to add |

Pilot run 1's reports use the older format: no unit-level tables, no source sections, no post-hoc table.

## Quickstart

Requirements: Python 3.11, Node.js 20+, git.

**Windows (PowerShell)**

```powershell
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -e ".[dev]"; pytest -q; cd ..
cd frontend; npm ci; npm test; cd ..
.\scripts\demo.ps1          # starts API + web app, opens http://localhost:5173, Ctrl+C stops both
```

**Linux / macOS**

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && pytest -q && cd ..
cd frontend && npm ci && npm test && cd ..
./scripts/demo.sh           # starts API + web app, opens http://localhost:5173, Ctrl+C stops both
```

No API key is needed for anything except the LLM compiler and a real evaluation run.

### Audit demo without any API key

```bash
cd backend && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
python -m app.audit.cli run ../fixtures/samples/sample_a_mm.ifc --out ../eval/runs/audit-demo
```

It prints a per-rule table and writes `report.json`, `report.html` and `issues.bcf`. In the web app the landing
page is at `/` and the checker at `/app`: pick "Sample A" (doors) or "Sample D" (rooms and stairs), or open
`/app?sample=sample_a_mm` directly. Screenshots are in `docs/screenshots/` (`landing-desktop.png`,
`app-sample-a.png`, `app-selected.png`).

### What to add to your model before submitting

```bash
cd backend                                    # with the venv active
python -m app.rulepack.cli readiness          # writes docs/readiness/niyam-data-readiness.ids
```

Open that IDS in any IDS checker (for example ifctester) against your IFC4 model before auditing it. It lists the data
NIYAM's rules need, and each requirement names the clauses it enables:

- `Pset_SpaceCommon.Category` on every IfcSpace, using one of the rules' Category values;
- `Pset_DoorCommon.FireExit` on every IfcDoor, plus `Qto_DoorBaseQuantities.Width` / `Height` and `OperationType`
  on exit doors;
- `Pset_BuildingCommon.OccupancyType` on the IfcBuilding.

The Category names are NIYAM's assumed profile (`docs/modelling-profile.md`), not a standard. A requirement that
reports PASS (0/0) found no element to check, which does not make the model ready. Body geometry for spaces and stair
flights is also needed and cannot be expressed in IDS.

### Reproduce the dry run (synthetic answers, no key)

```bash
cd backend                                    # with the venv active
python -m app.eval.cli --config ../eval/config.dryrun.yaml plan
python -m app.eval.cli --config ../eval/config.dryrun.yaml run --yes --dry-run
```

The report in `eval/results/dryrun-*/summary.md` starts with **"DRY RUN: synthetic responses, not model results"**.
Its numbers only show that the pipeline works; never quote them. For a real run see `docs/evaluation.md`
(preflight, plan with token estimate, then run).

## Limitations

- **Synthetic fixtures.** Dev, held-out and sample models are small generated boxes, not real buildings. The only
  real exports tried (two files of one buildingSMART sample scene, `docs/real-models.md`) carry too little data for
  any rule to check anything.
- **Drafts.** Every rule encodes one reading of a clause and none is human-reviewed yet
  (`docs/review/REVIEWER_GUIDE.md`).
- **Coverage.** The 25 units are every MBBL 2016 sentence found so far that fits a single-element template cleanly; the Stage 1 target of 40 to 60 clauses is not met (see `docs/spec-backlog.md` for why the rest do not fit).
- **Telangana: two units.** The Telangana rules leave room sizes, heights and doors to the National Building Code (Rule 15(a)(vi)). Two sentences of Rule 5 fit a template once Rule 5's heading (non-high-rise buildings below 18m) is dropped and noted: stilt floor height at least 2.5m (`TGBR2012-5#c`) and chowk / courtyard area at least 9sq.m (`TGBR2012-5#fxi`). They use assumed room Category names (Stilt, Chowk, Courtyard). Two units are a case study, not a sample: no rate is reported for them.
- **Single-element thresholds.** The templates check one value of one element (a door width, a room's area or
  height). Ratios, counts, distances and relations between elements are not encoded (`docs/spec-backlog.md`).
- **Ignored conditions.** Building-type exceptions (e.g. 2 m doorways in assembly buildings), room-use conditions
  and second thresholds in the same sentence are dropped and only noted for the reviewer.
- **Thresholds are checked against the text, not its meaning** (`docs/specgen.md`).
- **Millimetre geometry before the fix.** Until branch fix-mm-units the geometry helpers scaled millimetre models
  twice (rooms 10^6 too small in area, 10^3 too low), and the fixtures stored millimetre shapes 1000x too large, so the
  two cancelled on every fixture. Fixed and regenerated (`STATUS.md`). Run 2 and the Telangana case study predate the
  fix; their stored candidates were re-scored, not re-run, and 0 of 240 geometric outcomes changed
  (`eval/results/rescore-after-mm-fix/`). The fix was verified on a hand-written IFC file and one SketchUp export, not
  on Revit or ArchiCAD exports.
- **Small n.** 27 units: 25 MBBL (22 distinct), so every evaluation interval is wide, and 2 Telangana units, reported only as a case study with counts (`docs/evaluation.md`).

## More

- `docs/evaluation.md`: metrics, held-out fixtures, the first real run.
- `docs/specgen.md` and `docs/spec-backlog.md`: rule specs and what they cannot express.
- `docs/real-models.md`: two real IFC4 exports run through the audit, and what they lack.
- `docs/geometric-gate.md`: the Python sandbox and what it does not enforce.
- `docs/modelling-profile.md`: what an IFC model must contain to be checkable.
- `docs/review/`: the review sheet and the reviewer guide.
- `docs/frontend.md`: the web app, the 3D view, and why sample D once looked like one red wall.
- `cd frontend && npm run docs:pdf`: rebuilds the PDF versions of these documents that the landing page footer offers for reading and download.
- `cd frontend && npm run site-data`: regenerates every number the landing page shows from committed results.
- `python scripts/check_public_ready.py`: scans the tree and history for secrets and personal paths.
- `python scripts/check_numbers.py [--tests]`: checks every number in the README, STATUS, docs, submission pack and
  landing data against the committed results (also run by `backend/tests/test_check_numbers.py`).

## Team

Team **Abhyudaya**, B V Raju Institute of Technology (BVRIT), Narsapur, Telangana: Nikhil Mamilla, Yagna Sri Hasa,
G Nikhitha, D Sahithi and G Sahithi. Mentor: Dr. Lanke Pallavi, Associate Professor & Associate HoD.

Entry to the DBI 2026 Student Competition (CDCPIndia / buildingSMART India), theme "AI, Automation and Digital
Workflows" (secondary: Integrated BIM and Information Management). Finals: 17 Dec 2026, IIT Bombay.

## License

MIT (see `LICENSE`). Clause text is quoted from the publicly available MoHUA Model Building Bye-Laws 2016 and the
Telangana Building Rules 2012 (G.O.Ms.No.168) for research purposes; the source PDFs are not redistributed
(`rules/source/` is ignored). The two models in `fixtures/real/` are (C) buildingSMART International, CC BY 4.0,
redistributed unmodified with attribution (`fixtures/real/README.md`). The official buildingSMART IDS test cases
(CC BY-ND 4.0) are not redistributed: only findings from them are committed (`docs/notes-ids-official-testcases.md`).
No other buildingSMART sample files are in the repository.

Three UI components (Specular Button, Gooey Nav, Card Swap) are copied from React Bits under MIT + Commons Clause and
are excluded from NIYAM's MIT grant; every shipped package, font and data file is listed with its licence in
`THIRD_PARTY_NOTICES.md`. To cite NIYAM, see `CITATION.cff`.
