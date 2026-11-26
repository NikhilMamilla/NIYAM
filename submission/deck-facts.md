# Deck facts: every number the DBI 2026 Stage 2 deck may use

Each line gives the fact, the committed file it comes from, and the sentence it supports. Rates are written exactly as
the evaluation harness wrote them: `k/n = rate [Wilson 95% interval]`. `python scripts/check_numbers.py` checks this
file against the committed results; do not change a number here without changing its source.

Run ids: pilot run 1 `20261118T133025Z-4c4519`, headline run 2 `20261118T140452Z-5b7edb`, Telangana run
`20261118T180916Z-4b9c93`. Abbreviation: `R2` = `eval/results/20261118T140452Z-5b7edb/`.

## Problem

| Fact | Source | Supports |
|---|---|---|
| BIS withdrew NBC 2016 (SP 7:2016) with effect from 30 April 2026, replaced by the advisory NBCS 2026 (SP 7:2026) | `docs/sources.md` (secondary sources; Gazette not fetched) | "India's building code has just changed; the rules still reach officers as text." |
| From 1 October 2026, CORENET X submissions are mandatory in Singapore for new projects of 5,000 m² GFA and above | `docs/sources.md` (URA circular DC26-08) | "Model-based submission is already mandatory elsewhere." |
| IDS 1.0 was published as a final buildingSMART standard in June 2024 | `docs/sources.md` | "There is an open standard for machine-checkable data requirements." |
| Plans in most Indian cities are checked as 2D drawings; no open, machine-readable version of the bye-laws exists | `docs/sources.md` (softened, OBPS row) | "The checks are hidden in software or done by reading." Say "most cities"; do not name a vendor or a speed. |

## Pipeline

| Fact | Source | Supports |
|---|---|---|
| 445 clauses from MBBL 2016 and 55 clauses from the Telangana Building Rules 2012 (29 rules, 12 annexures, 14 appendices) | `rules/corpus/clause-ids.txt` | "We ingested two bye-laws, clause by clause." |
| 27 verbatim units: 25 MBBL 2016 and 2 Telangana | `docs/review/review-sheet.csv` | "27 sentences became machine checks." |
| Of the 25 MBBL units: 6 hand-written pilots and 19 from rule specs; 3 duplicates, so 22 distinct | `docs/review/review-sheet.csv`, `rules/specs/` | "Each check is one sentence; duplicates are counted once in the distinct view." |
| 7 IDS units and 20 geometric units (18 MBBL, 2 Telangana) | `docs/review/review-sheet.csv` | "Declared data goes to IDS 1.0; measured values go to a sandboxed Python check." |
| Rulepack v0: 6 rules (3 door IDS, 3 room/stair Python) | `rules/rulepack/v0/manifest.yaml` | "The audit app runs a small draft rulepack." |
| The gate allows up to 3 repair rounds | `R2/summary.md` (max repairs 3) | "A failed draft is sent back with the reason." |
| Outputs: JSON report, self-contained HTML report, BCF 2.1 issues; 4 verdicts passed / failed / unchecked / out_of_scope | `docs/audit.md` | "Every result goes back to the design tool as an issue." |

## Evaluation: run 2 (headline)

| Fact | Source | Supports |
|---|---|---|
| 2 open NVIDIA models: nemotron-3-ultra-550b-a55b and nemotron-3.5-lightning-30b-a3b; temperature 0.0, reasoning off, 3 repeats, max 3 repairs | `R2/slides-data.md` | "Two open models, each rule drafted three times, with and without the gate." |
| 415 model calls, 1,423,180 tokens | `R2/slides-data.md` | "What the headline run cost." |
| 75 items per model and mode (25 units x 3 repeats) | `R2/summary.md` | "n per cell." |
| **wrong_shipped, gated:** ultra 2/68 = 3% [1%, 10%]; lightning 0/50 = 0% [0%, 7%] | `R2/summary.md`, All units | "With the gate, few wrong rules reach the rulepack." |
| **wrong_shipped, ungated:** ultra 20/75 = 27% [18%, 38%]; lightning 31/75 = 41% [31%, 53%] | `R2/summary.md`, All units | "Without the gate, about a quarter to two fifths of shipped rules are wrong." |
| Counted per unit (more cautious): gated ultra 1/23 = 4% [1%, 21%], lightning 0/17 = 0% [0%, 18%]; ungated ultra 8/25 = 32% [17%, 52%], lightning 14/25 = 56% [37%, 73%] | `R2/summary.md`, Unit level | "The gap holds when each rule counts once." |
| The gate ships fewer: shipped 68/75 = 91% [82%, 95%] (ultra) and 50/75 = 67% [55%, 76%] (lightning); needs_human 7/75 = 9% [5%, 18%] and 25/75 = 33% [24%, 45%] | `R2/summary.md` | "The price of the gate: some drafts go to a person." |
| Held-out correct: gated ultra 66/75 = 88% [79%, 94%], ungated 55/75 = 73% [62%, 82%]; gated lightning 50/75 = 67% [55%, 76%], ungated 44/75 = 59% [47%, 69%] | `R2/summary.md` | "Correct on buildings the gate never saw." |
| Paired (same unit and repeat): ultra 13 gated-only vs 2 ungated-only correct; lightning 9 vs 3 | `R2/summary.md`, Paired | "On the same rule, the gate wins more pairs than it loses." Not a significance test. |
| Distinct rules (22 units): gated ultra 2/59 = 3% [1%, 12%], lightning 0/47 = 0% [0%, 8%]; ungated ultra 15/66 = 23% [14%, 34%], lightning 25/66 = 38% [27%, 50%] | `R2/summary.md`, Distinct rules only | "Removing duplicates does not change the picture." |
| By tier, ungated: IDS rules wrong_shipped 13/21 = 62% [41%, 79%] (ultra) and 17/21 = 81% [60%, 92%] (lightning); geometric 7/54 = 13% [6%, 24%] and 14/54 = 26% [16%, 39%] | `R2/summary.md`, Breakdown by tier | "Declared-data rules are where ungated drafts go wrong most." Only 7 IDS units: intervals are wide. |
| Pilot run 1: 1 repeat, 143 model calls, 496,888 tokens; gated ultra 1/22 = 5% [1%, 22%], ungated ultra 6/25 = 24% [11%, 43%] | `eval/results/20261118T133025Z-4c4519/summary.md`, `slides-data.md` | "A first pilot pointed the same way." Older report format. |
| **Do not claim** a difference between the two models; with 25 units every interval is wide | `R2/slides-data.md` (Caution line) | Caveat on every results slide. |

## Telangana case study

| Fact | Source | Supports |
|---|---|---|
| 2 Telangana units: TGBR2012-5#c (stilt floor height at least 2.5 m) and TGBR2012-5#fxi (chowk / courtyard at least 9 sq.m) | `docs/review/review-sheet.csv`, README | "A second jurisdiction through the same pipeline." |
| 31 model calls, 196,879 tokens, 3 repeats | `eval/results/20261118T180916Z-4b9c93/slides-data.md` | Run size. |
| With the gate: 10 shipped, all 10 shipped and held-out correct; without: 12 shipped, 6 shipped and held-out correct | `eval/results/20261118T180916Z-4b9c93/summary.md` (sum of the case-study table) | "Same pattern, too few to rate." Counts only: never a percentage. |
| Most of the Telangana rules concern plots and leave room sizes and heights to the National Building Code (Rule 15(a)(vi)) | README, Limitations | Why only 2 units. |

## Geometric fix and re-score

| Fact | Source | Supports |
|---|---|---|
| Bug: millimetre geometry was scaled twice (rooms 10^6 too small in area, 10^3 too low); fixtures stored shapes 1000x too large, so the two cancelled | `STATUS.md` | "We found and fixed a unit bug the tests could not see." |
| Hand-written IFC: a 2000 x 1200 mm room extruded 2750 mm measured 0.0000024 m2 and 0.00275 m before, 2.4 m2 and 2.75 m after | `backend/tests/test_length_units.py`, `STATUS.md` | "Proved on a file we wrote by hand." |
| Real SketchUp export (Building-Architecture.ifc, living room): 0.000018495 m2 and 0.0022 m before, 18.495 m2 and 2.2 m after | `backend/tests/test_length_units.py`, `docs/real-models.md` | "And on one real export." Not Revit, not ArchiCAD. |
| 41 millimetre fixtures regenerated (dev, held-out, sample D) | git history of commit "Fix the millimetre double scale…" | Scope of the fix. |
| Re-score: before the fix it reproduces every committed score (216 of 216 run 2 and 24 of 24 Telangana geometric items); after it, 0 of 240 geometric outcomes changed | `eval/results/rescore-after-mm-fix/README.md`, `after.json` | "The published numbers stand." Say "re-scored", never "re-run". |
| Shipped and held-out wrong, geometric only, all models and modes pooled: 21 of 199 shipped geometric items in run 2, 6 of 22 shipped geometric items in the Telangana run, the same before and after the fix | `eval/results/rescore-after-mm-fix/README.md` | Pooled counts across gated and ungated; not a headline rate. |

## Real-model readiness

| Fact | Source | Supports |
|---|---|---|
| 2 real buildingSMART IFC4 files (SketchUp, millimetres): Building-Architecture (0 doors, 2 spaces, 0 stair flights) and Building-Structural (0, 0, 0) | `docs/real-models.md` | "We tried real exports." |
| With a one-off diagnostic pack of all 27 draft rules (not rulepack v0, never shipped — see Pipeline above for the 6 that ship): Building-Architecture 0 passed, 0 failed, 38 unchecked; 8 rules checked nothing. Building-Structural: all 27 rules checked nothing | `docs/real-models.md` | "Nothing could pass or fail: the data was missing." |
| Why: the rooms declare no Pset_SpaceCommon.Category; there are no doors and no stair flights; no Pset_BuildingCommon.OccupancyType | `docs/real-models.md` | "The bottleneck is the data in the model, not the rules." |
| NIYAM writes a data-readiness IDS (`docs/readiness/niyam-data-readiness.ids`) a modeller can run first | `docs/real-models.md` | "What to add before submitting." |

## Honest limitations

- Decision aid, not a legal approval tool; no human domain expert has reviewed the rules yet; an AI second-opinion review (ChatGPT) is in `docs/review/` (`README.md`, statements).
- Every test building is synthetic; the two real files carry too little data to check (`docs/real-models.md`).
- Small n: 25 MBBL units (22 distinct), 3 repeats; no model difference may be claimed (`R2/slides-data.md`).
- Single-element thresholds only; building-type and use conditions are dropped and noted (`docs/spec-backlog.md`).
- Two reading-dependent units (MBBL2016-4.8.2#1, MBBL2016-5.4.1#b2) and the sensitivity table without them are post hoc
  (`R2/summary.md`, POST-HOC section).
- Telangana: 2 units, base text of G.O.Ms.No.168 with amendments not applied (`docs/sources.md`).
- The millimetre fix is verified on a hand-written file and one SketchUp export only.
- The repository is MIT throughout; its landing-page button, nav and card-stack components were originally
  adapted from React Bits (MIT + Commons Clause) and have since been rewritten as original code (`THIRD_PARTY_NOTICES.md`).

## Engineering checks

| Fact | Source | Supports |
|---|---|---|
| pytest: 545 passed; vitest: 46 passed; Playwright: 29 passed, plus 8 on the GitHub Pages build (end-to-end, incl. the demo script and the GitHub Pages build with no backend) | `STATUS.md`, Final test run | "Tested end to end." |
| Every BCF export of samples A to E passes the BCF 2.1 schemas | `submission/samples/README.md` | "Open BCF 2.1 output." |
| Lighthouse, built landing page: Accessibility 100, Best Practices 100, SEO 100 (desktop and mobile); Performance 58 desktop, 47 mobile | `STATUS.md`, Known issues | Only if asked; do not lead with it. |

## Roadmap (as on landing sheet A-11)

1. Expert review of every rule, starting with the disputed ones.
2. Site geometry, so setbacks and plot rules can be checked.
3. The National Building Code in the corpus, for room sizes and heights.
4. Tests on real exports from Revit, ArchiCAD and other tools.
