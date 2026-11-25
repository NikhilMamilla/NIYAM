# Phase 13 status (branch ui-redesign)

## Fixed on branch fix-mm-units: millimetre geometry was converted twice

**What the bug was.** `backend/app/geometry/helpers.py` (`_mesh`) multiplied the vertices that ifcopenshell returns by
the project length-unit scale (0.001 for millimetres). ifcopenshell 0.9 already returns metres, so a correctly written
millimetre model (one that stores 2000 mm as 2000.0, as authoring tools do) got room areas a million times too small and heights
a thousand times too small, and every room and stair rule failed it. The fixture builder (`geo_builders._prism`)
multiplied by 1000 before calling `ifcopenshell.api`, which converts SI to project units itself, so every committed
millimetre fixture stored its room and stair shapes 1000x too large. The two errors cancelled on every fixture,
which is why no test caught it.

Verified independently, with an IFC4 file written by hand (plain entities, no project helpers): a 2000 x 1200 mm
room extruded 2750 mm gave 0.0000024 m2 and 0.00275 m before the fix, 2.4 m2 and 2.75 m after, the same as the metre
version of the file. The fix was verified on that hand-written file and on one SketchUp export (below), not on Revit
or ArchiCAD exports. The "living room" of the real buildingSMART model went from 0.000018495 m2 and 0.0022 m to
18.495 m2 and 2.2 m (its geometry spans 4.95 x 3.8 x 2.2 m).

**What changed.** `_mesh` no longer rescales. `_prism` passes metres to `ifcopenshell.api`. The existing generators
regenerated the 41 millimetre fixtures that carry room or stair geometry (dev, held-out and sample D). No metre
fixture, door fixture or truth file changed (truth is derived arithmetically from the specs). Regression tests:
`backend/tests/test_length_units.py`. The pre-fix sample D is kept, never as a fixture, as
`fixtures/invalid/misscaled_rooms_mm.ifc`, to check that the viewer's wrong-unit notice still appears.

**Effect on committed results.** The headline run 2 (`20261118T140452Z-5b7edb`) and the Telangana case study
(`20261118T180916Z-4b9c93`) predate the fix. Their committed results are unchanged. Their stored final candidates
were re-scored offline (a re-score, not a re-run: the generate-verify-repair loop was not replayed) in
`eval/results/rescore-after-mm-fix/`. Before the fix the re-score reproduces every committed score (216 of 216 and
24 of 24 geometric items); after it, no item changes outcome. That is expected: on the fixtures the builder's 1000x and
the helper's 0.001 cancelled exactly, so every candidate saw the same metre values, and the gate's messages never
include measured values. A live re-run would therefore face the same verdicts and messages; it would differ only by the
models' own randomness.

## Done

- Stage 1: 3D framing fixed for any model size; room edges mapped by mesh id (see docs/frontend.md).
- Stage 2: design system (tokens, self-hosted IBM Plex, base components), PRODUCT.md, surface brief.
- Stage 3: site data generated from committed files (`npm run site-data`), cross-checked against the CSVs.
- Stage 4: landing page at `/`, 12 sections, every number from site-data.json.
- Stage 5: dashboard at `/app` with plain-language statuses, rule filters, detail panel, tour, deep links.
- Stage 6: 3D stage (sky, ground, fog, sun shadows on High quality, auto-orbit, preset views, hover tips).
- Stage 7: tsc, vitest, build, backend pytest, Playwright (workers=1) and check_public_ready run.

## Not done or limited

- The regulatory dates in `CONTEXT` (same file) come from the brief and were not checked against sources.
- Run backend pytest and Playwright one after the other: run at the same time on this machine they
  produced three failures (cause not investigated) that all passed when re-run alone.

## Next

- Review branch fix-mm-units; decide from the re-score whether a live re-run of run 2 is worth the calls.
- Fill in the team details; review the landing copy.
