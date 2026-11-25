# Deliberately invalid files (never fixtures)

Nothing here is a dev, held-out or sample fixture, and no loader globs this folder: each file is named by one test.

- `ifc2x3_minimal.ifc`: an IFC2X3 file, to check that non-IFC4 uploads are refused (`frontend/e2e/audit.spec.ts`).
- `misscaled_rooms_mm.ifc`: sample D as built before the millimetre fix (branch fix-mm-units): a millimetre project
  whose room and stair shapes are stored 1000x too large. It checks that the 3D view still shows its
  "drawn more than 200 m across" notice (`frontend/e2e/viewer-framing.spec.ts`). Its audit results are meaningless.
