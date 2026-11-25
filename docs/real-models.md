# Real IFC models: what the audit could check

Two real authoring-tool exports were run through the existing audit, with no LLM involved. **No compliance claim is
made for any real building.** A rule that checks nothing says nothing about whether the building complies.

## What we tried

| File | Source | Licence | Schema | Tool | Length unit | IfcDoor | IfcSpace | IfcStairFlight |
|---|---|---|---|---|---|---|---|---|
| Building-Architecture.ifc | buildingSMART Certification-datasets, IFC 4.0.2.1 Simple-Scene | CC BY 4.0 | IFC4 | SketchUp 2026 + IFC manager 5.6.0 | millimetre | 0 | 2 | 0 |
| Building-Structural.ifc | same scene, structural discipline | CC BY 4.0 | IFC4 | SketchUp 2026 + IFC manager 5.6.0 | millimetre | 0 | 0 | 0 |
| example.ifc | That Open engine_web-ifc `examples/` | MPL-2.0 repository | IFC2X3 | EXPRESS Data Manager | - | - | - | - |

`example.ifc` is IFC2X3. The audit accepts IFC4 only, and converting it was out of scope, so it was skipped and
deleted. The IfcOpenShell repository's test files (`src/bonsai/test/files`) are small feature tests, not building
models. The two buildingSMART files are committed under `fixtures/real/` with attribution (`fixtures/real/README.md`).

Other contents of Building-Architecture.ifc: 4 IfcWall, 3 IfcSlab, 3 IfcBuildingElementProxy, 1 IfcRoof,
1 IfcChimney, 1 IfcFurniture and 1 IfcSpatialZone. The two spaces ("living room", "entry hall") have geometry but no
property sets, and the IfcBuilding has no `Pset_BuildingCommon.OccupancyType`.

## Audit results

The audit was run with rulepack v0 (6 rules), then with a temporary pack of all 27 draft rules. That pack was v0 plus
the 21 spec units' gold artifacts, each added through `rulepack add --gate` (all 21 accepted). It lived in a scratch
folder and adds nothing to the committed rulepack, so its report still shows the version "v0".

| File | Rules | passed | failed | unchecked | out_of_scope | Rules that checked nothing |
|---|---|---|---|---|---|---|
| Building-Architecture | v0 (6) | 0 | 0 | 4 | 0 | 4 (3 door rules, 1 stair rule) |
| Building-Architecture | all 27 | 0 | 0 | 38 | 0 | 8 (7 door rules, 1 stair rule) |
| Building-Structural | v0 (6) | 0 | 0 | 0 | 0 | 6 |
| Building-Structural | all 27 | 0 | 0 | 0 | 0 | 27 |

Per rule on Building-Architecture: every room rule (2 in v0; 19 of the 27: 17 MBBL and both Telangana units)
reported both spaces unchecked, each time for the same reason: "This space does not declare its category
(Pset_SpaceCommon.Category), so it is unknown whether the rule applies." The door rules (5.4.1#b, #b2, #c, 5.4.2#1,
4.24.7.2#b/#c/#f) and the stair rule (4.17.2#A) found no elements to check.

### Room geometry before and after the millimetre fix

Both files are millimetre projects. Before branch fix-mm-units the helpers scaled their geometry twice. The audit
with rulepack v0, re-run after the fix, gives the same counts as the table above, and element by element the same
verdicts and reasons as before it (the 27-rule pack was not re-run): the two room rules return "unchecked" because the
rooms declare no Category, which each check reads before it calls a measuring helper, and the stair rule finds no
IfcStairFlight, so the fixed geometry helpers are never reached on these two files and the missing data, not the unit,
decides the verdict. Measured directly with the helpers (`tests/test_length_units.py`),
the living room (geometry spanning 4.95 x 3.8 x 2.2 m):

| | floor area | height |
|---|---|---|
| before the fix | 0.000018495 m2 | 0.0022 m |
| after the fix | 18.495 m2 | 2.2 m |

## What a real model must carry for NIYAM to check it

See `docs/modelling-profile.md` for the full profile.

| Rule family | Needs | Present in these files |
|---|---|---|
| Room area and height (19 units) | IfcSpace with Body geometry and `Pset_SpaceCommon.Category` set to one of the profile's names (Habitable, Kitchen, Store, Stilt, ...) | spaces with geometry, but no Category, so every room rule is unchecked |
| Exit-door width and height (3 units) | IfcDoor with `Pset_DoorCommon.FireExit = TRUE` and `Qto_DoorBaseQuantities.Width` / `.Height` | no IfcDoor |
| Exit-door operation (4 units) | IfcDoor with FireExit, and an IfcDoorType with `OperationType` | no IfcDoor |
| Stair width (1 unit) | IfcStairFlight with Body geometry, and `Pset_BuildingCommon.OccupancyType` on the IfcBuilding | no stair flight, no OccupancyType |

Mapping a tool's own room names ("living room") to the profile's Category values is not done. A model must declare
the Category, or a pre-processing step (not built) must add it.

## What to add to your model before submitting

`python -m app.rulepack.cli readiness` writes `docs/readiness/niyam-data-readiness.ids`, one IDS 1.0 file generated
from the rule specs and rulepack v0. Each requirement's instructions name the clauses it enables. ifctester results:

| Requirement | sample A (synthetic) | Building-Architecture.ifc (real) |
|---|---|---|
| Spaces declare a profile Category | PASS (0/0): no spaces | **FAIL (0/2)**: living room, entry hall have no Pset_SpaceCommon |
| Doors declare Pset_DoorCommon.FireExit | FAIL (10/12) | PASS (0/0): no doors |
| Exit doors carry Qto_DoorBaseQuantities.Width | FAIL (7/8) | PASS (0/0) |
| Exit doors carry Qto_DoorBaseQuantities.Height | PASS (8/8) | PASS (0/0) |
| Exit doors declare OperationType | PASS (8/8) | PASS (0/0) |
| Buildings declare Pset_BuildingCommon.OccupancyType | FAIL (0/1) | FAIL (0/1) |

PASS (0/0) means no element applied, not that the model is ready. The Category names are NIYAM's assumed profile, not
a standard: a real model has to adopt them (or a mapping step, not built, has to add them).

## Limits

- Two files from one synthetic scene, exported by one tool. Revit, ArchiCAD and other exporters were not tried.
- The Category names are this project's convention. No real export here uses them.
