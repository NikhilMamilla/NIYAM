# Synthetic sample buildings

`fixtures/samples/sample_a_mm.ifc` (millimetre project, 12 doors) and
`fixtures/samples/sample_b_m.ifc` (metre project, 10 doors) are **synthetic test models**. They are
not real Indian buildings and say nothing about real-world compliance: each is a bare IFC4
project / site / building with two storeys ("Ground floor", "First floor") and doors carrying only
the data the v0 rulepack reads (`Pset_DoorCommon.FireExit`, `IfcDoor.OperationType`,
`Qto_DoorBaseQuantities.Width`). There is no geometry.

They seed every case the pilot rules distinguish: exit doors that meet the rules (including one at exactly
1.0 m), an exit door narrower than 1.0 m, revolving, sliding and overhead (`ROLLINGUP`) exit doors,
non-exit doors that would break the rules but are out of scope, doors with no `FireExit` property
(unchecked), and in sample A an exit door without a width quantity (unchecked for 5.4.1#b only).

`fixtures/samples/sample_c_no_fireexit_mm.ifc` (4 doors, none with `FireExit`) exists to show the
"incomplete" state: nothing can be checked, so the audit must never report it as compliant.
`fixtures/invalid/ifc2x3_minimal.ifc` is an IFC2X3 file used to test that non-IFC4 uploads are
refused; it is deliberately not a sample.

`<name>.truth.json` lists, for every door, the expected verdict under every rulepack rule. These
verdicts are written by hand in `backend/app/fixtures/samples.py`, not computed by the audit engine,
and `backend/tests/test_samples.py` requires the audit to match them element by element.

Regenerate (deterministic, byte-identical) from `backend/`:

```bash
python ../scripts/build_sample_buildings.py
```

## Geometric samples (D and E)

`sample_d_rooms_stairs_mm` (millimetres, 9 spaces + 5 stair flights) and `sample_e_rooms_stairs_m` (metres,
8 spaces + 4 flights) seed the three geometric rules (`MBBL2016-4.5.2#1` bathroom area, `4.3.1.1#1` habitable
room height, `4.17.2#A` residential stair width). Every geometric rule sees a passing, a failing, an unchecked
(no geometry, or no `Category` / `OccupancyType` data) and an out-of-scope element, including values exactly at
the bound (1.8 m², 2.75 m, 1.0 m). The `*.truth.json` files list the expected verdict of every element and rule,
written by hand in `app/fixtures/samples.py` independently of the audit, which `tests/test_geometric_samples.py`
compares element by element. They contain no doors, so the three door rules report "nothing checked" on them.
All geometry is simple extruded boxes; none of it is a real building.
