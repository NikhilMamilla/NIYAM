# NIYAM rule review sheet

Fill in the empty columns of `review-sheet.csv` (it opens in Excel): **decision** is `accept`, `modify` or `reject`; give your name and the date. For `modify`, write the corrected reading and/or threshold. Every rule below is a draft machine encoding of the quoted clause.

## MBBL2016-4.17.2#A (geometric, page 75)

**Rule text:** The minimum width of staircase shall be as follows: A Residential buildings (dwellings) 1.0 m

**Machine reading:** IfcStairFlight in an IfcBuilding with Pset_BuildingCommon.OccupancyType=Residential: flight width (local Y extent of the flight geometry) >= 1.0 m. Ambiguity: 'width of staircase' taken as flight width, not clear width between handrails; other building types (1.5 m, 2.0 m) and the row-housing note (0.75 m) are not encoded; flights in other occupancy types are out of scope.

**Threshold:** at least 1.0 m (computed: stair_flight_width_m)

**Applies to:** IfcStairFlight, selected inside the check; needs Pset_BuildingCommon.OccupancyType

<details><summary>Full clause text</summary>

```
4.17.2 Minimum width
The minimum width of staircase shall be as follows:
A Residential buildings (dwellings) 1.0 m
NOTE — For row housing with 2
storeys, the min. width of shall be 0.75
B Residential hotel buildings 1.5 m
C Assembly buildings like auditoria, 2.0 m
theatres and cinemas
D Educational building 1.5 m
E Institutional buildings 2.0 m
F All other buildings 1.5 m
```
</details>

## MBBL2016-4.3.1.1#1 (geometric, page 69)

**Rule text:** The height of all rooms for human habitation shall not be less than 2.75 m measured from the surface of the floor to the lowest point of the ceiling (bottom of slab)

**Machine reading:** IfcSpace with Pset_SpaceCommon.Category=Habitable: vertical extent of the space geometry (floor to underside of slab) >= 2.75 m. Ambiguity: assumes the modelled space spans floor surface to slab soffit; the beam (2.4 m), pitched-roof (average height) and air-conditioned (2.4 m) provisions in the following sentences are not encoded; applies to residential/business/mercantile only (4.3.1.2), building type not checked.

**Threshold:** at least 2.75 m (computed: element_height_m)

**Applies to:** IfcSpace, selected inside the check; needs Pset_SpaceCommon.Category

<details><summary>Full clause text</summary>

```
4.3.1.1 The height of all rooms for human habitation shall not be less than 2.75 m measured
from the surface of the floor to the lowest point of the ceiling (bottom of slab)
provided that the minimum clear headway under any beam shall not be less than 2.4 m.
In the case of pitched roof, the average height of rooms shall not be less than 2.75 m.
The minimum clear head room under a beam, folded plates or eaves shall be 2.4 m. In
the case of air-conditioned rooms, a height of not less than 2.4 m measured from the
surface of the floor to the lowest point of air-conditioning duct or the false ceiling shall
be provided.
```
</details>

## MBBL2016-4.5.2#1 (geometric, page 70)

**Rule text:** The area of a bathroom shall not be less than 1.8 m2

**Machine reading:** IfcSpace with Pset_SpaceCommon.Category=Bathroom: floor area computed from the space geometry (down-facing faces of the body mesh) >= 1.8 m2. Ambiguity: the same sentence adds 'with a minimum width of 1.2 m' (not encoded: width of a non-rectangular footprint is not defined by the clause); 'bathroom' is mapped to the Category convention; geometric area vs declared Qto NetFloorArea not distinguished by the clause.

**Threshold:** at least 1.8 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace, selected inside the check; needs Pset_SpaceCommon.Category

<details><summary>Full clause text</summary>

```
4.5.2 Size
The area of a bathroom shall not be less than 1.8 m2 with a minimum width of 1.2 m.
The floor area of water-closet shall be 1.1 m2 with a minimum width of 0.9 m. If bath
and water-closet are combined, its floor area shall not be less than 2.8 m2 with a
minimum width of 1.2 m.
```
</details>

## MBBL2016-5.4.1#b (ids, page 100)

**Rule text:** No exit doorway shall be less than 1m in width.

**Machine reading:** IfcDoor with FireExit=TRUE: Qto_DoorBaseQuantities.Width >= 1.0 m. Uses the quantity, not OverallWidth: IDS attribute bounds are not unit-converted (see docs/notes-ids-expressiveness.md). Ambiguity: clear vs leaf vs overall width not specified.

**Threshold:** at least 1.0 m

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, Qto_DoorBaseQuantities.Width

<details><summary>Full clause text</summary>

```
5.4.1 Doorways
a. Every doorway shall open into an enclosed stairway, a horizontal exit, on a corridor
or passageway providing continuous and protected means of egress.
b. No exit doorway shall be less than 1m in width. Doorways shall be not less than 2
m in height. Doorways for bathrooms, water closet, stores etc. shall be not less than
0.75m wide.
c. Exit doorways shall open outwards, that is, away from the room but shall not
obstruct the travel along any exit. No door, when opened, shall reduce the required
width of stairway or landing to less than 0.9m, overhead or sliding doors shall not
be installed.
d. Exit door shall not open immediately upon a flight or stairs, a landing equal to at
least the width of the door shall be provided in the stairway at each doorway, level
of landing shall be the same as that of the floor which it serves.
e. Exit doorways shall be openable from the side which they serve without the use of a
key.
f. Mirrors shall not be placed in exit ways or exit doors to avoid confusion regarding
the direction of exit.
```
</details>

## MBBL2016-5.4.1#c (ids, page 100)

**Rule text:** overhead or sliding doors shall not be installed

**Machine reading:** IfcDoor with FireExit=TRUE: OperationType not in {SLIDING_TO_LEFT, SLIDING_TO_RIGHT, DOUBLE_DOOR_SLIDING, ROLLINGUP}. Ambiguity: scope (exit doorways) inferred from sub-item c; 'overhead' mapped to ROLLINGUP only; fragment of a comma-spliced sentence whose first half (0.9m landing width) is geometric.

**Threshold:** none

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, OperationType

<details><summary>Full clause text</summary>

```
5.4.1 Doorways
a. Every doorway shall open into an enclosed stairway, a horizontal exit, on a corridor
or passageway providing continuous and protected means of egress.
b. No exit doorway shall be less than 1m in width. Doorways shall be not less than 2
m in height. Doorways for bathrooms, water closet, stores etc. shall be not less than
0.75m wide.
c. Exit doorways shall open outwards, that is, away from the room but shall not
obstruct the travel along any exit. No door, when opened, shall reduce the required
width of stairway or landing to less than 0.9m, overhead or sliding doors shall not
be installed.
d. Exit door shall not open immediately upon a flight or stairs, a landing equal to at
least the width of the door shall be provided in the stairway at each doorway, level
of landing shall be the same as that of the floor which it serves.
e. Exit doorways shall be openable from the side which they serve without the use of a
key.
f. Mirrors shall not be placed in exit ways or exit doors to avoid confusion regarding
the direction of exit.
```
</details>

## MBBL2016-5.4.2#1 (ids, page 100)

**Rule text:** Revolving door shall not be provided as a means of fire exit.

**Machine reading:** IfcDoor with Pset_DoorCommon.FireExit=TRUE: OperationType must not be REVOLVING. Ambiguity: 'means of fire exit' is mapped to the FireExit flag.

**Threshold:** none

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, OperationType

<details><summary>Full clause text</summary>

```
5.4.2 Revolving Doors
Revolving door shall not be provided as a means of fire exit.
```
</details>
