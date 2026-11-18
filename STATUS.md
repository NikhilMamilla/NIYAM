# Phase 13 status (branch ui-redesign)

## Blocked: needs your decision (backend and fixtures, not changed on this branch)

**Millimetre geometry is converted twice.** `backend/app/geometry/helpers.py` line 90 multiplies the vertices that
ifcopenshell returns by the project length-unit scale (0.001 for millimetres), with the comment "geometry comes back
in project length units". The installed ifcopenshell returns metres. The fixture builder writes the shapes of rooms
and stairs in millimetre files 1000x too large, which cancels the error for every committed sample and fixture.

Evidence (run in memory, nothing changed):

| Room D-B-01 in sample D | stored profile | helper area | helper height |
|---|---|---|---|
| as committed | 2,000,000 x 1,200,000 mm, 2,750,000 mm high | 2.4 m2 | 2.75 m |
| correct millimetre geometry | 2,000 x 1,200 mm, 2,750 mm high | 0.0000024 m2 | 0.00275 m |

Consequences:

- A correctly modelled millimetre IFC file (the usual case for Revit, ArchiCAD and SketchUp exports) gets room
  areas a million times too small and heights a thousand times too small, so every room and stair rule fails it.
  The real buildingSMART model was not affected only because its rooms have no Category (all unchecked).
- Sample D (and the millimetre dev/held-out fixtures of geometric units) store their shapes 1000x too large, so the
  3D view of sample D shows rooms kilometres across. The viewer now frames it, draws it as stored and says so.
- Evaluation results are internally consistent (gold checks and candidates ran on the same fixtures), but the
  geometric rules' behaviour on real millimetre models is wrong.

Proposed fix (one change in each place, then regenerate the millimetre samples and fixtures and re-run the suite):
drop the extra `scale` in `helpers.py` (`_verts`), and make the fixture builder write millimetre shapes in
millimetres. This changes audit semantics, fixtures and possibly the gold behaviour, which this phase's rules
forbid, so it was not done.

## Done

- Stage 1: 3D framing fixed (see docs/frontend.md, "Why sample D looked like one red wall").

## Next

See the stage list in the Phase 13 brief.
