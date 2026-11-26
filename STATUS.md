# Status: submission-v2 (branch final-lock), 25 November 2026

NIYAM is frozen for the DBI 2026 Stage 2 deck. Everything below is final unless listed under Known issues.

## Final

- **Corpus and rules.** 445 MBBL 2016 clauses and 55 Telangana clauses (`rules/corpus/clause-ids.txt`); 27 verbatim
  units: 25 MBBL 2016 and 2 Telangana; rulepack v0: 6 rules (3 door IDS, 3 room/stair Python). Every rule is a draft;
  no human domain expert has reviewed the rules yet, though an AI second-opinion review (ChatGPT) is in
  `docs/review/`.
- **Results.** Pilot run 1 (`20261118T133025Z-4c4519`, 143 model calls), headline run 2 (`20261118T140452Z-5b7edb`,
  415 model calls) and the Telangana case study (`20261118T180916Z-4b9c93`, 31 model calls), all in `eval/results/`.
  `submission/deck-facts.md` lists every number the deck may use with its source file.
- **Millimetre fix.** Fixed and merged (below); run 2 and the Telangana run were re-scored, not re-run: 0 of 240
  geometric outcomes changed (`eval/results/rescore-after-mm-fix/`).
- **One source of truth.** `scripts/check_numbers.py` checks every number in the README, STATUS, docs, the submission
  pack and the landing data against the committed results; the landing page reads its statements, context facts,
  roadmap and real-model summary from the README and docs (`npm run site-data`), and `src/landing/Landing.test.tsx`
  fails if the page and the docs disagree. `scripts/check_images.py` checks every published image.
- **Submission pack** (`submission/`): deck facts, demo script (executed by `frontend/e2e/demo-script.spec.ts`), run
  guide, sample outputs A to E with BCF validated against the BCF 2.1 schemas, slide screens.
- **Licences.** `THIRD_PARTY_NOTICES.md`, `CITATION.cff`; regulatory facts with sources in `docs/sources.md`.

## The millimetre double-scale bug (fixed)

**What the bug was.** `backend/app/geometry/helpers.py` (`_mesh`) multiplied the vertices that ifcopenshell returns by
the project length-unit scale (0.001 for millimetres). ifcopenshell 0.9 already returns metres, so a correctly written
millimetre model (one that stores 2000 mm as 2000.0, as authoring tools do) got room areas a million times too small
and heights a thousand times too small, and every room and stair rule failed it. The fixture builder
(`geo_builders._prism`) multiplied by 1000 before calling `ifcopenshell.api`, which converts SI to project units
itself, so every committed millimetre fixture stored its room and stair shapes 1000x too large. The two errors
cancelled on every fixture, which is why no test caught it.

Verified independently, with an IFC4 file written by hand (plain entities, no project helpers): a 2000 x 1200 mm
room extruded 2750 mm gave 0.0000024 m2 and 0.00275 m before the fix, 2.4 m2 and 2.75 m after, the same as the metre
version of the file. The fix was verified on that hand-written file and on one SketchUp export, not on Revit or
ArchiCAD exports. The "living room" of the real buildingSMART model went from 0.000018495 m2 and 0.0022 m to
18.495 m2 and 2.2 m (its geometry spans 4.95 x 3.8 x 2.2 m; `backend/tests/test_length_units.py`).

**What changed.** `_mesh` no longer rescales. `_prism` passes metres to `ifcopenshell.api`. The existing generators
regenerated the 41 millimetre fixtures that carry room or stair geometry (dev, held-out and sample D). No metre
fixture, door fixture or truth file changed. The pre-fix sample D is kept, never as a fixture, as
`fixtures/invalid/misscaled_rooms_mm.ifc`, to check that the viewer's wrong-unit notice still appears.

**Effect on committed results.** Run 2 and the Telangana case study predate the fix; their committed results are
unchanged. Their stored final candidates were re-scored offline (a re-score, not a re-run: the generate-verify-repair
loop was not replayed). Before the fix the re-score reproduces every committed score (216 of 216 and 24 of 24
geometric items); after it, no item changes outcome, because on the fixtures the builder's 1000x and the helper's
0.001 cancelled exactly and the gate's messages never include measured values.

## Known issues

1. **NBCS 2026 date from secondary sources.** The Gazette of India notice could not be fetched (TLS certificate
   error); the 30 April 2026 withdrawal rests on two agreeing secondary reports (`docs/sources.md`). The OBPS / AutoDCR
   sentence is softened and not verified verbatim; the IDS 1.0 year comes from Wikipedia (the release page showed the
   day, not the year).
2. **Telangana amendments.** The units use the 2012 base text; a 2026 amendment is reported to raise the high-rise
   threshold from 18 m to 21 m, which Rule 5's heading depends on. TGBR2012-5#fxi is unaffected either way (its
   9 sq.m minimum also holds under Telangana's own high-rise courtyard rule); TGBR2012-5#c's 2.5 m stilt-floor
   minimum is unverified either way, because no Telangana high-rise stilt-floor rule is in the ingested corpus to
   compare against (`docs/sources.md`). Not applied, not reviewed.
3. **Landing page performance.** Lighthouse on the built landing page (25 November 2026): desktop Performance 65,
   Accessibility 100, Best Practices 100, SEO 100; mobile Performance 45, Accessibility 100, Best Practices 100, SEO 100
   (up from 58/47 before this stage, after switching the button's idle light from an animated gradient position to
   an opacity pulse, which is compositor-only). The remaining main-thread cost (desktop 520 ms, mobile ~4 s of
   blocking time) is page weight (1,822 DOM elements, one long single-page site) and a pre-existing non-composited
   animation on the demo-step buttons (sheet A-09, unrelated to this stage); not investigated further.
4. **BCF viewpoints** carry component selections only (no camera, no snapshot); the files pass the BCF 2.1 schemas
   but were not opened in a third-party BCF viewer.
5. **Hosted: demo mode only.** GitHub Pages publishes the site (`docs/deploy.md`); with no backend it shows the
   engine's saved results for the 5 samples and cannot audit an uploaded file. The Render API is prepared
   (`render.yaml`) but not deployed. Locally, `scripts/demo.ps1` creates `backend\.venv` itself with Python 3.11 or
   3.12 if it is missing (never a newer default `python`); confirmed in a clean clone on a machine whose default
   `python` is 3.13.
6. **Run backend pytest and Playwright one after the other**: run at the same time on this machine they produced
   failures that passed when re-run alone (cause not investigated).
7. **Coverage.** The Stage 1 target of 40 to 60 clauses is not met (25 MBBL units; `docs/spec-backlog.md`).

## Reproduce

From the repository root, Windows PowerShell, with `backend\.venv` (Python 3.11) and `frontend\node_modules`:

```powershell
cd backend; .venv\Scripts\python.exe -m pytest -q; cd ..                    # backend tests
cd frontend; npx vitest run; npx tsc -p tsconfig.json; npm run build; cd ..   # frontend tests, types, build
cd frontend; npx playwright test --workers=1; cd ..                          # end-to-end, one at a time (rewrites the screenshots)
backend\.venv\Scripts\python.exe scripts\check_public_ready.py              # secrets and personal paths, tree and history
backend\.venv\Scripts\python.exe scripts\check_numbers.py --tests           # every quoted number and test count
backend\.venv\Scripts\python.exe scripts\check_images.py                    # every published image
```

Offline re-score after the millimetre fix (no LLM calls). It reads the local attempt logs in `eval/runs/`, which are
not committed, so it runs only on the machine that holds them. From `backend\` with the venv active, on this branch:

```powershell
python ..\scripts\rescore_after_mm_fix.py score after    # re-scores the stored candidates with the fixed code
python ..\scripts\rescore_after_mm_fix.py compare        # refuses unless the committed before.json reproduces the committed scores
```

`score before` needs the code before the fix (commit `53b0cd6`, for example in a separate `git worktree`); its
output is committed as `eval/results/rescore-after-mm-fix/before.json`.

## Final test run (26 November 2026, branch deploy, one suite after another)

| Check | Result |
|---|---|
| Backend | pytest: 545 passed (534 before the deployment work, plus the demo-data drift test and the public API mode) |
| Frontend unit | vitest: 46 passed |
| Types and build | tsc clean; `npm run build` and `npm run build:pages` built |
| End-to-end | Playwright: 29 passed (workers=1; 28 before plus the demo-video spec); GitHub Pages build with no backend (`playwright.static.config.ts`): 8 passed |
| check_public_ready | no secrets in the tree or the full history; 0 personal-path and 0 file warnings |
| check_numbers --tests | 1,067 numbers checked in 30 files, 0 mismatches |
| check_images | 30 referenced images, 29 published files, 0 problems |
| Clean-clone install | confirmed on a true `git clone` of this branch, default `python` 3.13: `scripts/demo.ps1` created `backend\.venv` with `py -3.11` and both servers came up; a sample audit ran correctly |

Before this branch, `main` at `8a10194` had 527 passing in pytest and 39 in vitest.
