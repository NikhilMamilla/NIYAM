# NIYAM rule review sheet

Fill in the empty columns of `review-sheet.csv` (it opens in Excel): **decision** is `accept`, `modify` or `reject`; give your name and the date. For `modify`, write the corrected reading and/or threshold. Every rule below is a draft machine encoding of the quoted clause.

## MBBL2016-4.8.2#1 (geometric, page 72)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The size of a store room, where provided in a residential building, shall be not less than 3 m2.

**Machine reading:** Store rooms (Category Store) must have a floor area of at least 3 m2. "Size" is read as floor area. NOT encoded: the condition "where provided in a residential building"; store rooms in other building types are checked too.

**Threshold:** at least 3 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Store; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

**Reading-dependent:** The clause says 'where provided in a residential building'; the spec drops that condition and checks store rooms in every building. Both models' candidates kept the residential condition, which never applies to the test buildings (they declare no OccupancyType). Decide which reading is intended.

<details><summary>Full clause text</summary>

```
4.8.2 Size
The size of a store room, where provided in a residential building, shall be not less
than 3 m2.
```
</details>

## MBBL2016-5.4.1#b2 (ids, page 100)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** Doorways shall be not less than 2 m in height.

**Machine reading:** Exit doors (Pset_DoorCommon.FireExit = TRUE) must have Qto_DoorBaseQuantities.Height of at least 2 m. Inclusive. AMBIGUITY: the sentence says "Doorways", read as exit doorways because clause 5.4.1 is about exits; non-exit doors are not checked. Clear opening vs leaf vs frame height is not specified.

**Threshold:** at least 2 m

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, Qto_DoorBaseQuantities.Height; not in a rulepack

**Reading-dependent:** The sentence says 'Doorways' (all doors); the spec reads it as exit doors only (Pset_DoorCommon.FireExit = TRUE) because clause 5.4.1 is about exits. Candidates that applied the 2 m height to every door failed the test buildings, which contain a lower non-exit door. Decide which reading is intended.

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

## MBBL2016-3.16.1#a (geometric, page 67)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The height of the rooms shall be not less than 3.6 metres from the floor to soffit

**Machine reading:** Rooms of a creche or day-care facility (Category Creche) must be at least 3.6 m high (vertical extent of the space geometry, floor to soffit). NOT encoded: the 1.86 sqm of floor area per child in the same sentence (needs an occupant count). AMBIGUITY: "the rooms" is read as every room of the creche.

**Threshold:** at least 3.6 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Creche; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
3.16.1 Creche/Day Care facilities
As per factories Act, 1948 a Creche/Day care facility has to be provided for any
organization/establishment employing more than 15 women for their kids upto the age
of 5.
a) The height of the rooms shall be not less than 3.6 metres from the floor to soffit
and there shall not be less than 1.86 sqm of floor area / child to be accommodated
and maintaining adequate ventilation by the circulation of fresh air.
b) There is a minimum of one toilet and one wash hand basin for every 10 children
over the age of two years. (refer notes under Table 4.21)
c) The minimum staffing ratios for care shall be 1:4 children
d) Monitoring- There is a necessity of minimum two supervisor on continuous duty.
Chapter Note:
For projects proposed within the Prohibited and Regulated areas as defined by AMASR Act
2010, the Development regulations of Height, FAR, Coverage and any other controls stipulated
in Chapter-3 and Chapter-5 of MBBL shall be superseded by site specific Heritage Bye-Laws
prepared and notified by the Competent Authority (NMA) under the AMASR Act. NOC shall
have to be obtained as per the Rules framed under the said Act by submission of required
documents as may be necessary vide rules, including “Heritage Impact Assessment” report, if
so necessitated by the NMA.
4. GENERAL BUILDING REQUIREMENTS
AND SERVICES
```
</details>

## MBBL2016-4.10.4#a (geometric, page 72)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** Every basement shall be in every part at least 2.4 m in height from the floor to the underside of the roof slab or ceiling

**Machine reading:** Basement spaces (Category Basement) must be at least 2.4 m high. AMBIGUITY: "in every part" asks for the minimum height everywhere, but the helper measures the vertical extent (the maximum for a non-prismatic space); this only agrees for spaces with a flat floor and ceiling. "Roof slab or ceiling" is not distinguished.

**Threshold:** at least 2.4 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Basement; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.10.4 The basement shall have the following requirements:
a) Every basement shall be in every part at least 2.4 m in height from the floor to the
underside of the roof slab or ceiling;
b) Adequate ventilation shall be provided for the basement. The ventilation
requirements shall be the same as required by the particular occupancy according
to byelaws. Any deficiency may be met by providing adequate mechanical
ventilation in the form of blowers, exhaust fans, air-conditioning systems, etc;
c) The minimum height of the ceiling of any basement shall be 0.9m and the
maximum, 1.2 m above the average surrounding ground level;
d) Adequate arrangements shall be made such that surface drainage does not enter the
basement;
e) The walls and floors of the basement shall be watertight and be so designed that
the effects of the surrounding soil and moisture, if any, are taken into account in
design and adequate damp proofing treatment is given; and
f) The access to the basement shall be separate from the main and alternative
staircase providing access and exit from higher floors.
g) Where the staircase is continuous in the case of buildings served by more than one
staircase, the same shall be of enclosed type serving as a fire separation from the
basement floor and higher floors. Open ramps shall be permitted if they are
constructed within the building line subject to the provision of (d). The exist
requirements in basements shall comply with the provisions of Part 4 ‘Fire and
Life Safety’
```
</details>

## MBBL2016-4.13#1 (geometric, page 73)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The size of cabins shall not be less than 3.0 m2

**Machine reading:** Cabins (Category Cabin) must have a floor area of at least 3.0 m2. NOT encoded: "with a minimum width of 1.0 m", the 0.75 m clear passages, the 18.5 m travel distance and the 2.2 m maximum height of unventilated cabins.

**Threshold:** at least 3.0 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Cabin; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.13 Cabin
The size of cabins shall not be less than 3.0 m2 with a minimum width of 1.0 m. The
clear passages within the divided space of any floor shall not be less than 0.75 m and
the distance from the farthest space in a cabin to any exit shall not be more than 18.5
m. In case the sub-divided cabin does not derive direct lighting and ventilation from
any open spaces/ mechanical means, the maximum height of the cabin shall be 2.2 m.
```
</details>

## MBBL2016-4.17.2#A (geometric, page 75)

**Source:** MoHUA Model Building Bye-Laws 2016

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

## MBBL2016-4.22#1 (geometric, page 76)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The minimum area for office room/shop or any other space to be used as workspace shall not be less than 6.0 sq m.

**Machine reading:** Offices, shops and other workspaces (Category Office, Shop or Workspace) must have a floor area of at least 6.0 m2. NOT encoded: "with a minimum width of 2.1 m" and the clause heading's condition "Non-residential buildings" (the building type is not checked; the room categories are assumed to imply it).

**Threshold:** at least 6.0 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Office or Shop or Workspace; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.22 Non-residential buildings
The minimum area for office room/shop or any other space to be used as workspace
shall not be less than 6.0 sq m. with a minimum width of 2.1 m.
```
</details>

## MBBL2016-4.24.7.2#b (ids, page 80)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** No exit doorways shall be less than 1m in width

**Machine reading:** Exit doors (Pset_DoorCommon.FireExit = TRUE) must have Qto_DoorBaseQuantities.Width of at least 1 m. Inclusive ("not less than"). NOT encoded: "except assembly and institutional buildings where Doorway shall not be less than 2 m" (building type is not checked, so a 1.5 m exit in an assembly building passes). Duplicates MBBL2016-5.4.1#b. Clear vs leaf vs overall width is not specified.

**Threshold:** at least 1 m

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, Qto_DoorBaseQuantities.Width; not in a rulepack

**Claimed duplicate of:** MBBL2016-5.4.1#b (confirm or reject in comments)

<details><summary>Full clause text</summary>

```
4.24.7.2 Doorways
a. Every doorway shall open into an enclosed stairway, a horizontal exit, on a corridor
or passageway providing continuous and protected means of egress.
b. No exit doorways shall be less than 1m in width except assembly and institutional
buildings where Doorway shall not be less than 2 m.
c. Exit doorways shall open outwards, that is away from the room but shall not obstruct
the travel along any exit. No door when opened shall reduce the required width of
stairway or landing to less than 0.90 m Overhead or sliding door shall not be
installed.
Note: In the case of buildings where there is a central corridor, the doors of rooms shall open inwards
to permit smooth flow of traffic in the corridor
d. Exit door shall not open immediately upon a flight of stairs. A landing equal to at
least, the width of the door shall be provided in the stairway at each doorway. Level
of landings shall be the same as that of the floor, which it serves.
e. Exit doorways shall be openable from the side, which they serve without the use of a
key.
f. Revolving doors shall not to be provided as means of fire exit.
g. Mirrors shall not be placed in exit ways or exit doors to avoid confusion regarding
the direction of exit.
```
</details>

## MBBL2016-4.24.7.2#c (ids, page 80)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** Overhead or sliding door shall not be installed.

**Machine reading:** Exit doors (FireExit = TRUE) must not be sliding (SLIDING_TO_LEFT, SLIDING_TO_RIGHT, DOUBLE_DOOR_SLIDING) or overhead (ROLLINGUP). AMBIGUITY: the sentence has no subject restriction; it is read as applying to exit doorways because it sits in sub-item c about exit doorways. "Overhead" mapped to ROLLINGUP only. Duplicates MBBL2016-5.4.1#c.

**Threshold:** none (forbidden operations: SLIDING_TO_LEFT, SLIDING_TO_RIGHT, DOUBLE_DOOR_SLIDING, ROLLINGUP)

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, OperationType; not in a rulepack

**Claimed duplicate of:** MBBL2016-5.4.1#c (confirm or reject in comments)

<details><summary>Full clause text</summary>

```
4.24.7.2 Doorways
a. Every doorway shall open into an enclosed stairway, a horizontal exit, on a corridor
or passageway providing continuous and protected means of egress.
b. No exit doorways shall be less than 1m in width except assembly and institutional
buildings where Doorway shall not be less than 2 m.
c. Exit doorways shall open outwards, that is away from the room but shall not obstruct
the travel along any exit. No door when opened shall reduce the required width of
stairway or landing to less than 0.90 m Overhead or sliding door shall not be
installed.
Note: In the case of buildings where there is a central corridor, the doors of rooms shall open inwards
to permit smooth flow of traffic in the corridor
d. Exit door shall not open immediately upon a flight of stairs. A landing equal to at
least, the width of the door shall be provided in the stairway at each doorway. Level
of landings shall be the same as that of the floor, which it serves.
e. Exit doorways shall be openable from the side, which they serve without the use of a
key.
f. Revolving doors shall not to be provided as means of fire exit.
g. Mirrors shall not be placed in exit ways or exit doors to avoid confusion regarding
the direction of exit.
```
</details>

## MBBL2016-4.24.7.2#f (ids, page 80)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** Revolving doors shall not to be provided as means of fire exit.

**Machine reading:** Exit doors (FireExit = TRUE) must not have OperationType REVOLVING. "Means of fire exit" mapped to the FireExit flag. The clause's grammar ("shall not to be") is verbatim. Duplicates MBBL2016-5.4.2#1.

**Threshold:** none (forbidden operations: REVOLVING)

**Applies to:** IfcDoor where Pset_DoorCommon.FireExit is TRUE; needs Pset_DoorCommon.FireExit, OperationType; not in a rulepack

**Claimed duplicate of:** MBBL2016-5.4.2#1 (confirm or reject in comments)

<details><summary>Full clause text</summary>

```
4.24.7.2 Doorways
a. Every doorway shall open into an enclosed stairway, a horizontal exit, on a corridor
or passageway providing continuous and protected means of egress.
b. No exit doorways shall be less than 1m in width except assembly and institutional
buildings where Doorway shall not be less than 2 m.
c. Exit doorways shall open outwards, that is away from the room but shall not obstruct
the travel along any exit. No door when opened shall reduce the required width of
stairway or landing to less than 0.90 m Overhead or sliding door shall not be
installed.
Note: In the case of buildings where there is a central corridor, the doors of rooms shall open inwards
to permit smooth flow of traffic in the corridor
d. Exit door shall not open immediately upon a flight of stairs. A landing equal to at
least, the width of the door shall be provided in the stairway at each doorway. Level
of landings shall be the same as that of the floor, which it serves.
e. Exit doorways shall be openable from the side, which they serve without the use of a
key.
f. Revolving doors shall not to be provided as means of fire exit.
g. Mirrors shall not be placed in exit ways or exit doors to avoid confusion regarding
the direction of exit.
```
</details>

## MBBL2016-4.3.1.1#1 (geometric, page 69)

**Source:** MoHUA Model Building Bye-Laws 2016

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

## MBBL2016-4.4.1#1 (geometric, page 70)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The height of a kitchen measured from the surface of the floor to the lowest point in the ceiling (bottom of slab) shall not be less than 2.75 m

**Machine reading:** Kitchens (IfcSpace with Pset_SpaceCommon.Category = Kitchen) must be at least 2.75 m high, measured as the vertical extent of the space geometry, which assumes the modelled space runs from floor surface to the underside of the slab. "Not less than" read as inclusive. NOT encoded: the exception "except for the portion to accommodate floor trap of the upper floor" (a local lowering of the ceiling would make the whole kitchen fail or pass depending on modelling).

**Threshold:** at least 2.75 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Kitchen; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.4.1 Height
The height of a kitchen measured from the surface of the floor to the lowest point in
the ceiling (bottom of slab) shall not be less than 2.75 m, except for the portion to
accommodate floor trap of the upper floor.
```
</details>

## MBBL2016-4.5.1#1 (geometric, page 70)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The height of a bathroom or water-closet measured from the surface of the floor to the lowest point in the ceiling (bottom of slab) shall not be less than 2.1 m.

**Machine reading:** Bathrooms, water-closets and combined bath/WC rooms (Category Bathroom, WaterCloset or CombinedBathWC) must be at least 2.1 m high (vertical extent of the space geometry, floor to slab soffit). Inclusive. Ambiguity: a combined bath/WC room is assumed to be covered by "bathroom or water-closet"; false ceilings are not distinguished.

**Threshold:** at least 2.1 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Bathroom or WaterCloset or CombinedBathWC; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.5.1 Height
The height of a bathroom or water-closet measured from the surface of the floor to the
lowest point in the ceiling (bottom of slab) shall not be less than 2.1 m.
```
</details>

## MBBL2016-4.5.2#1 (geometric, page 70)

**Source:** MoHUA Model Building Bye-Laws 2016

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

## MBBL2016-4.5.2#2 (geometric, page 70)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The floor area of water-closet shall be 1.1 m2

**Machine reading:** Water-closets (Category WaterCloset) must have a floor area of at least 1.1 m2 (footprint of the space geometry). AMBIGUITY: the clause says "shall be 1.1 m2", read as a minimum; a reviewer may read it as an exact size. NOT encoded: "with a minimum width of 0.9 m".

**Threshold:** at least 1.1 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is WaterCloset; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.5.2 Size
The area of a bathroom shall not be less than 1.8 m2 with a minimum width of 1.2 m.
The floor area of water-closet shall be 1.1 m2 with a minimum width of 0.9 m. If bath
and water-closet are combined, its floor area shall not be less than 2.8 m2 with a
minimum width of 1.2 m.
```
</details>

## MBBL2016-4.5.2#3 (geometric, page 70)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** If bath and water-closet are combined, its floor area shall not be less than 2.8 m2

**Machine reading:** A combined bath and water-closet room (Category CombinedBathWC) must have a floor area of at least 2.8 m2. Inclusive. The "combined" condition is mapped to a separate Category value, which the modelling profile has to define. NOT encoded: "with a minimum width of 1.2 m".

**Threshold:** at least 2.8 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is CombinedBathWC; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.5.2 Size
The area of a bathroom shall not be less than 1.8 m2 with a minimum width of 1.2 m.
The floor area of water-closet shall be 1.1 m2 with a minimum width of 0.9 m. If bath
and water-closet are combined, its floor area shall not be less than 2.8 m2 with a
minimum width of 1.2 m.
```
</details>

## MBBL2016-4.7.1#1 (geometric, page 71)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** It shall have a minimum height of 2.2 m.

**Machine reading:** A mezzanine floor (Category Mezzanine) must be at least 2.2 m high. "It" is read as the mezzanine floor from the section title 4.7 Mezzanine Floor. AMBIGUITY: whether the height is clear height above the mezzanine or below it is not stated; the encoding uses the vertical extent of the modelled mezzanine space.

**Threshold:** at least 2.2 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Mezzanine; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.7.1 Height
It shall have a minimum height of 2.2 m.
```
</details>

## MBBL2016-4.7.2#1 (geometric, page 71)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The minimum size of the mezzanine floor, if it is to be used as a living room, shall not be less than 9.5 m2.

**Machine reading:** A mezzanine floor must have a floor area of at least 9.5 m2. AMBIGUITY / NOT encoded: the condition "if it is to be used as a living room" is ignored, so every space with Category Mezzanine is checked; a reviewer may want a separate Category for living-room mezzanines. The one-third-of-plinth-area limit in the next sentence is not encoded.

**Threshold:** at least 9.5 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Mezzanine; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.7.2 Size
The minimum size of the mezzanine floor, if it is to be used as a living room, shall not
be less than 9.5 m2.
The aggregate area of such mezzanine floor in a building shall in no case exceed one-
third the plinth area of the building.
```
</details>

## MBBL2016-4.8.1#1 (geometric, page 72)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The height of a store room shall be not less than 2.2 m.

**Machine reading:** Store rooms (Category Store) must be at least 2.2 m high (vertical extent of the space geometry). Inclusive.

**Threshold:** at least 2.2 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Store; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.8.1 Height
The height of a store room shall be not less than 2.2 m.
```
</details>

## MBBL2016-4.9.1#1 (geometric, page 72)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The height of a garage shall be not less than 2.4 m.

**Machine reading:** Garages (Category Garage) must be at least 2.4 m high. Inclusive. AMBIGUITY: private and public garages are not distinguished.

**Threshold:** at least 2.4 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Garage; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
4.9.1 Height
The height of a garage shall be not less than 2.4 m.
```
</details>

## MBBL2016-5.4.1#b (ids, page 100)

**Source:** MoHUA Model Building Bye-Laws 2016

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

**Source:** MoHUA Model Building Bye-Laws 2016

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

**Source:** MoHUA Model Building Bye-Laws 2016

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

## MBBL2016-7.1#1 (geometric, page 119)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** The minimum internal height of workrooms shall not be less than 4.5 m.

**Machine reading:** Factory workrooms (Category Workroom) must be at least 4.5 m high. NOT encoded: the clause is about industrial buildings (7.1); the building type is not checked, only the room category. Clear internal height vs floor-to-slab is not distinguished.

**Threshold:** at least 4.5 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Workroom; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
7.1 Industrial Buildings (Factories, Workshops, etc.)
1. The relevant provisions contained in the Factory Act. 1948 shall apply for the
construction of factory buildings. The minimum internal height of workrooms shall not
be less than 4.5 m. measured from the floor level to the lowest point in the ceiling
provided that this bye-laws shall not apply to room intended for storage, godowns and
the like purposes but only in rooms occupied by workers for purposes of manufacture.
In case of small factories, employing less than 50 workers for purposes of
manufacturing and carrying on a class of manufacturing covered under the flatted
factories and service industries, as given in the Master Plan/Development Plan, the
Authority may allow minimum height upto 3.66 m.
2. Parking space provisions as provide in development code of Master Plan/Development
Plan.
3. Requirements of water supply, drainage and sanitary installation shall be as per Table
4.6, 4.7 and 4.21, but in no case less than 1 W.C. and one urinal shall be permitted.
a) Notwithstanding the provision of exits requirements as per Bye-law section
11.8 each working room shall be provided with adequate number of exits not
less than two in number.
b) No exit shall be less than 1.2 m. in width and 2.1 m. in height and doors of
such exit shall be so arranged that it can be opened easily from inside.
c) No staircase, lobby corridors or passage shall be less than 1.2 m. in width.
In addition to the requirement in this part, provisions contained in chapter-3 will be
followed.
4. There shall be provided at all time for each person employed in any room of factory at
least 3.5 sq m. of floor space exclusive to that occupied by the machinery and a
breathing space of at least 15 cum. (Further the provision of part VIII section 1
lighting and ventilation of National Building code of India shall be followed).
5. The effluent from industries (industrial and biological in nature) shall be treated and
shall be of quality to the satisfaction of the concerned local bodies before letting out
the same into a watercourse or municipal drain.
```
</details>

## MBBL2016-7.2#1 (geometric, page 119)

**Source:** MoHUA Model Building Bye-Laws 2016

**Rule text:** A minimum room height for classroom in all schools and other institutions shall not be less than 3.0 m.

**Machine reading:** Classrooms (Category Classroom) must be at least 3.0 m high. NOT encoded: the 3.0 m clear height under balconies or girders and the 2.75 m head room under beams in the same clause (need beam geometry).

**Threshold:** at least 3.0 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Classroom; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
7.2 Educational Building (School/Colleges)
1. No basement or cellar room shall be designed, constructed, altered, converted or used
for the purpose of study or instruction.
2. Every such building, exceeding two storeys in height shall be constructed of fire
resisting material throughout.
3. The minimum size of a cellar room, study room or room used for purposes of
instruction shall be 5.5 m. x 4.5 m. and no part of such room shall be distant more than
7.5 m. from an external wall abutting on the requisite open space. Every such room
shall have minimum ventilation to the extent of 1/5th of its floor area.
4. A minimum of 1.0 sq m. of net floor space per student shall be provided. A central hall
will not be counted in the accommodation, nor will a class room for cookery, laundry,
manual instruction, drawing or science. The number of students in such building shall
be calculated on this basis for the purpose of this section.
5. Every assembly room, gymnasium shall have a clear height of 3.6 m. except under a
girder which may project 0.6 m. below the required ceiling height.
A clear internal height under balcony or a girder shall not be less than 3.0 m.
A minimum room height for classroom in all schools and other institutions shall not be
less than 3.0 m. The minimum head room under beams shall be 2.75 m.
6. Exit requirements shall conform to bye-laws section 11.7 and 11.8 (Chapter-11). No
door shall be less than 1.2 m. in width and 2.20 m. in height.
7. Requirement of water supply, drainage and sanitary installation shall conform to Table
4.6, 4.7, 4.11, 4.12 and 4.13 of Chapter-4.
8. A playground shall be provided as per norms.
```
</details>

## TGBR2012-5#c (geometric, page 9)

**Source:** Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied)

**Rule text:** Height of stilt floor shall not be less than 2.5m.

**Machine reading:** Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied), Rule 5(c). Stilt floor spaces (Pset_SpaceCommon.Category Stilt, an assumed name) must be at least 2.5 m high; "not less than" read as inclusive. The stilt floor is modelled as an IfcSpace, like MBBL basements; a stilt floor that is only an IfcBuildingStorey is not checked. NOT encoded: (1) Rule 5's heading limits it to non-high-rise buildings ("Buildings below 18m in height inclusive of Stilt / Parking Floor"); the building height is not checked. (2) The preceding sentence describes the stilt floor as "meant for parking"; its use is not checked. (3) The next sentence sets 4.5m for parking floors "where mechanical system and lift are provided"; such a floor passes this unit at 2.5m. (4) Height is the space's vertical extent, floor to slab, not a clear height under beams.

**Threshold:** at least 2.5 m (computed: element_height_m)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Stilt; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
5. PERMISSIBLE SETBACKS & HEIGHT STIPULATIONS FOR ALL TYPES
OF NON-HIGH RISE BUILDINGS
(Buildings below 18m in height inclusive of Stilt / Parking Floor):
(a) The height of buildings permissible in a given site / plot shall be subject
to restrictions given in Annexure - I to II.
(b) The minimum setbacks and permissible height as per Table - III and
other conditions stipulated below shall be followed.
TABLE – III
Building Line or Minimum Front Setback
Minimum
Height to be left (in m)
Plot Size setbacks
(in m) Abutting Road Width
Sl. (in Sqm) Parking on
Permissi Up Above Above Above
No. Above – provision remaining
ble to 12m & 18m & 24m & Above
Up to sides
Up to 12 up to up to up to 30m
(in m)
m 18m 24 m 30m
1 2 3 4 5 6 7 8 9 10
Less than
1 7 1.5 1.5 3 3 3 -
50
7 1.5 1.5 3 3 3 -
2 50-100 -
10 1.5 1.5 3 3 3 0.5
100 -
3 - 10 1.5 1.5 3 3 3 1.0
200
7
2 3 3 4 5 1.0
200 - Stilt
4
300 floor 10
2 3 3 5 6 1.5
7
3 4 5 6 7.5 1.5
300 - Stilt
5
400 floor 12
3 4 5 6 7.5 2.0
7
3 4 5 6 7.5 2.0
400 - Stilt
6
500 floor 12
3 4 5 6 7.5 2.5
7
3 4 5 6 7.5 2.5
Stilt
* 500 -
12
7 floor 3 4 5 6 7.5 3.0
750
15
3 4 5 6 7.5 3.5
7
Stilt + 3 4 5 6 7.5 3.0
750 - One
12
8 3 4 5 6 7.5 3.5
1000 Cellar
floor 15 3 4 5 6 7.5 4.0
7
3 4 5 6 7.5 3.5
Stilt + 12
3 4 5 6 7.5 4.0
1000 -
9 2 Cellar
1500 15
3 4 5 6 7.5 5.0
floors
18**
3 4 5 6 7.5 6.0
7
3 4 5 6 7.5 4.0
Stilt +
1500 -
15
10 2 Cellar 3 4 5 6 7.5 5.0
2500
floors
18**
3 4 5 6 7.5 6.0
Stilt + 7
3 4 5 6 7.5 5.0
2 or
Above 15
11 more 3 4 5 6 7.5 6.0
2500
Cellar
18**
3 4 5 6 7.5 7.0
floors
(c) Stilt Floor meant for parking is excluded from the permissible height in
the above Table. Height of stilt floor shall not be less than 2.5m. In case
of parking floors where mechanical system and lift are provided, height
of such parking floor shall not be less than 4.5m.
(d) *In case of commercial buildings proposed in plots having an extent of
500-750sq.m cellar floor for parking may be considered subject to
condition that required parking shall be fulfilled as per Table-V of rule-13
and feasibility on ground.
(e) **Buildings of height above 15m and below 18m in Sl.Nos.9, 10 and 11
above, shall be permitted only if such plots abut minimum 12m wide
roads only.
(f) Other conditions:
(i) The setbacks are to be left after leaving the affected area of the plot
/ site, if any, for road widening.
(ii) Where a site abuts more than one road, then the front setback
should be insisted towards the bigger road width and for the
remaining side or sides, the setback as at Column-10 shall be
insisted. In case of individual residential buildings the option is given
to the applicant to propose front setback on one of the roads. In
such case he shall not have access from the other side / sides. On
the other side / sides the applicant can leave the setback either as
per the required front setback based on the road width or to provide
the side setback as given in Column-10.
(iii) A strip of at least 1m greenery / lawn along the frontage of the site
within the front setback shall be developed and maintained with
greenery.
(iv) For Plots above 300sq.m in addition to (iii) above, a minimum 1m
wide continuous green planting strip in the periphery on remaining
sides are required to be developed and maintained within the
setback.
(v) For all residential / institutional / industrial plots above 750sq.m, in
addition to (iii) and (iv) above, 5% of the site area to be developed
as organized open space and be utilized as greenery, tot lot or soft
landscaping etc., and shall be provided over and above the
mandatory setbacks. Such organized open space could be in more
than one location and shall be of a minimum width of 3m with a
minimum area of 15sq.m at each location.
(vi) If the strip of greenery / lawn and the organized open space (tot lot)
are not maintained, 10% of additional Property Tax every year
would be imposed as penalty by the Sanctioning Authority till the
condition is fulfilled.
(vii) In all plots 750sq.m and above, provision shall be made for
earmarking an area of 3m X 3m for the purpose of setting of public
utilities like distribution transformer, etc. within the owner’s site
subject to mandated public safety requirements.
(viii) In case of plots 300 - 750sq.m, it is permitted to transfer up to 1m
of setback from any one side to any other side without exceeding
overall permissible plinth area. The transfer of setback from front
setback is not allowed.
(ix) In case of plots above 750sq.m, it is permitted to transfer up to 2m
of setback from any one side to any other side without exceeding
overall permissible plinth area, subject to maintaining of a minimum
2.5m setback on other side and a minimum building line. The
transfer of setback from front setback is not allowed.
(x) For narrow plots having extent not more than 400sq.m and where
the length is 4 times of the width of the plot, the setbacks on sides
may be compensated in front and rear setbacks so as to ensure that
the overall aggregate setbacks are maintained in the site, subject to
maintaining a minimum of side setback of 1m in case of buildings of
height up to 10m and minimum of 2m in case of buildings of height
above 10m and up to 15m without exceeding overall permissible
plinth area. (This Rule shall not be applicable for made-up plots).
(xi) Where the lighting and ventilation of a building is through the means
of a chowk or inner courtyard or interior open space / duct, such
open space shall be open to sky and of area at least 9sq.m and no
side shall be less than 2m. Such open spaces / ducts may be
allowed above stilt floor.
(xii) The space between 2 blocks shall not be less than the side setback
of the tallest block as mentioned in Table - III and this shall not be
considered for organised open space (tot lot).
(xiii) Where all the owners of sites along an abutting road come forward
for widening of the road by undertaking preparation of a Road
Development Plan which would improve circulation in the area and
duly approved by the competent authority, and by leaving the area
affected in the widening of such road free of cost and implement it
within one year, then higher height of the corresponding widened
road width would be considered for such sites.
(xiv) Splay at road junctions, including ‘Y’ junctions shall be provided as
follows. The area of such splay would be deemed to form part of
the road junction.
Sl.No Road Width (in m) Splay / Offset (in m)
1 Less than 12 3 X 3
2 Above 12 up to 24 4.5 X 4.5
3 Above 24 6 X 6
(xv) As per the provisions of the Andhra Pradesh Fire Service Act, 1999,
Residential buildings of height more than 18 m, Commercial
buildings of height 15m and above and buildings of public
congregation like Educational Buildings, Cinema Theatres, Function
Halls and other Assembly Buildings on plot area of 500Sq.m. and
above or of height above 6m are required to obtain prior clearance
from Andhra Pradesh State Disasters Response & Fire Services
Department from fire safety point of view.
(xvi) Stepped type buildings or incremental type buildings may be
allowed only in respect of individual residential or educational /
institutional buildings and such incremental development would be
considered only after a minimum time period of 5 years.
(xvii) For the purpose of these Rules, the following conversion from
M.K.S. and F.P.S. system shall be reckoned for the road widths
only:
(1) 3m = 10ft (2) 6m = 20ft (3) 7.5m = 25ft (4) 9m = 30ft
(5) 12m = 40ft (6) 15m = 50ft (7) 18m = 60ft (8) 24m = 80ft
(9) 30m = 100ft (10) 45m = 150ft (11) 60m = 200ft.
(xviii) All building applications for sanction of building permission for
construction of above 10m height shall be accompanied with the
following details:
(a) Report of Soil Test / Geo-technical Investigation Report issued
after personal inspection by Institution / Consultant
empanelled with / licenced by the local authority.
(b) Structural designs and drawings prepared duly taking the soil
bearing capacity into consideration and certified by qualified
Structural Engineer / Consultant Firm empanelled with / licenced
by the local authority. The Structural Engineer / Consultant Firm
is held responsible for defect in the design.
(c) Building Plan and Application shall be invariably signed by the
owner of the property, builder if any, the Architect and the
Structural Engineer who designed the structure. They shall give
their present and permanent addresses.
(d) If the construction is being taken up by a builder, an attested
copy of the registered agreement entered between the owner of
the property and the builder shall be submitted. In case of any
changes in the agreement at a later date, a copy of the same
shall also be submitted to the local authority.
(e) An undertaking on a Stamp Paper of Rs.100/-duly signed by the
owner and builder specifying that no flat or built-up area shall be
given possession to the purchaser / tenant unless they obtain the
occupancy certificate from the local authority and provide all
regular service connections.
(f) Contractor / Builders / Developer / Owner shall submit All Risks
Insurance Policy for the construction period.
```
</details>

## TGBR2012-5#fxi (geometric, page 9)

**Source:** Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied)

**Rule text:** Where the lighting and ventilation of a building is through the means of a chowk or inner courtyard or interior open space / duct, such open space shall be open to sky and of area at least 9sq.m and no side shall be less than 2m.

**Machine reading:** Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied), Rule 5(f)(xi). Chowk or inner-courtyard spaces (Pset_SpaceCommon.Category Chowk or Courtyard, assumed names) must have a floor area of at least 9 sq.m; "at least" is inclusive. NOT encoded: (1) "no side shall be less than 2m" (no width helper); (2) "open to sky"; (3) the condition that lighting and ventilation are through this space: every Chowk or Courtyard space is checked; (4) ducts and "interior open space" without one of the two Category values; (5) Rule 5's heading (non-high-rise buildings below 18m). Rule 7(a)(xv) requires 25sq.m and 3m for high-rise buildings; that unit is not created because without its heading it would fail non-high-rise buildings, while this 9sq.m minimum also holds for high-rise buildings (25 >= 9).

**Threshold:** at least 9 m2 (computed: space_floor_area_m2)

**Applies to:** IfcSpace where Pset_SpaceCommon.Category is Chowk or Courtyard; needs Pset_SpaceCommon.Category and body geometry; not in a rulepack

<details><summary>Full clause text</summary>

```
5. PERMISSIBLE SETBACKS & HEIGHT STIPULATIONS FOR ALL TYPES
OF NON-HIGH RISE BUILDINGS
(Buildings below 18m in height inclusive of Stilt / Parking Floor):
(a) The height of buildings permissible in a given site / plot shall be subject
to restrictions given in Annexure - I to II.
(b) The minimum setbacks and permissible height as per Table - III and
other conditions stipulated below shall be followed.
TABLE – III
Building Line or Minimum Front Setback
Minimum
Height to be left (in m)
Plot Size setbacks
(in m) Abutting Road Width
Sl. (in Sqm) Parking on
Permissi Up Above Above Above
No. Above – provision remaining
ble to 12m & 18m & 24m & Above
Up to sides
Up to 12 up to up to up to 30m
(in m)
m 18m 24 m 30m
1 2 3 4 5 6 7 8 9 10
Less than
1 7 1.5 1.5 3 3 3 -
50
7 1.5 1.5 3 3 3 -
2 50-100 -
10 1.5 1.5 3 3 3 0.5
100 -
3 - 10 1.5 1.5 3 3 3 1.0
200
7
2 3 3 4 5 1.0
200 - Stilt
4
300 floor 10
2 3 3 5 6 1.5
7
3 4 5 6 7.5 1.5
300 - Stilt
5
400 floor 12
3 4 5 6 7.5 2.0
7
3 4 5 6 7.5 2.0
400 - Stilt
6
500 floor 12
3 4 5 6 7.5 2.5
7
3 4 5 6 7.5 2.5
Stilt
* 500 -
12
7 floor 3 4 5 6 7.5 3.0
750
15
3 4 5 6 7.5 3.5
7
Stilt + 3 4 5 6 7.5 3.0
750 - One
12
8 3 4 5 6 7.5 3.5
1000 Cellar
floor 15 3 4 5 6 7.5 4.0
7
3 4 5 6 7.5 3.5
Stilt + 12
3 4 5 6 7.5 4.0
1000 -
9 2 Cellar
1500 15
3 4 5 6 7.5 5.0
floors
18**
3 4 5 6 7.5 6.0
7
3 4 5 6 7.5 4.0
Stilt +
1500 -
15
10 2 Cellar 3 4 5 6 7.5 5.0
2500
floors
18**
3 4 5 6 7.5 6.0
Stilt + 7
3 4 5 6 7.5 5.0
2 or
Above 15
11 more 3 4 5 6 7.5 6.0
2500
Cellar
18**
3 4 5 6 7.5 7.0
floors
(c) Stilt Floor meant for parking is excluded from the permissible height in
the above Table. Height of stilt floor shall not be less than 2.5m. In case
of parking floors where mechanical system and lift are provided, height
of such parking floor shall not be less than 4.5m.
(d) *In case of commercial buildings proposed in plots having an extent of
500-750sq.m cellar floor for parking may be considered subject to
condition that required parking shall be fulfilled as per Table-V of rule-13
and feasibility on ground.
(e) **Buildings of height above 15m and below 18m in Sl.Nos.9, 10 and 11
above, shall be permitted only if such plots abut minimum 12m wide
roads only.
(f) Other conditions:
(i) The setbacks are to be left after leaving the affected area of the plot
/ site, if any, for road widening.
(ii) Where a site abuts more than one road, then the front setback
should be insisted towards the bigger road width and for the
remaining side or sides, the setback as at Column-10 shall be
insisted. In case of individual residential buildings the option is given
to the applicant to propose front setback on one of the roads. In
such case he shall not have access from the other side / sides. On
the other side / sides the applicant can leave the setback either as
per the required front setback based on the road width or to provide
the side setback as given in Column-10.
(iii) A strip of at least 1m greenery / lawn along the frontage of the site
within the front setback shall be developed and maintained with
greenery.
(iv) For Plots above 300sq.m in addition to (iii) above, a minimum 1m
wide continuous green planting strip in the periphery on remaining
sides are required to be developed and maintained within the
setback.
(v) For all residential / institutional / industrial plots above 750sq.m, in
addition to (iii) and (iv) above, 5% of the site area to be developed
as organized open space and be utilized as greenery, tot lot or soft
landscaping etc., and shall be provided over and above the
mandatory setbacks. Such organized open space could be in more
than one location and shall be of a minimum width of 3m with a
minimum area of 15sq.m at each location.
(vi) If the strip of greenery / lawn and the organized open space (tot lot)
are not maintained, 10% of additional Property Tax every year
would be imposed as penalty by the Sanctioning Authority till the
condition is fulfilled.
(vii) In all plots 750sq.m and above, provision shall be made for
earmarking an area of 3m X 3m for the purpose of setting of public
utilities like distribution transformer, etc. within the owner’s site
subject to mandated public safety requirements.
(viii) In case of plots 300 - 750sq.m, it is permitted to transfer up to 1m
of setback from any one side to any other side without exceeding
overall permissible plinth area. The transfer of setback from front
setback is not allowed.
(ix) In case of plots above 750sq.m, it is permitted to transfer up to 2m
of setback from any one side to any other side without exceeding
overall permissible plinth area, subject to maintaining of a minimum
2.5m setback on other side and a minimum building line. The
transfer of setback from front setback is not allowed.
(x) For narrow plots having extent not more than 400sq.m and where
the length is 4 times of the width of the plot, the setbacks on sides
may be compensated in front and rear setbacks so as to ensure that
the overall aggregate setbacks are maintained in the site, subject to
maintaining a minimum of side setback of 1m in case of buildings of
height up to 10m and minimum of 2m in case of buildings of height
above 10m and up to 15m without exceeding overall permissible
plinth area. (This Rule shall not be applicable for made-up plots).
(xi) Where the lighting and ventilation of a building is through the means
of a chowk or inner courtyard or interior open space / duct, such
open space shall be open to sky and of area at least 9sq.m and no
side shall be less than 2m. Such open spaces / ducts may be
allowed above stilt floor.
(xii) The space between 2 blocks shall not be less than the side setback
of the tallest block as mentioned in Table - III and this shall not be
considered for organised open space (tot lot).
(xiii) Where all the owners of sites along an abutting road come forward
for widening of the road by undertaking preparation of a Road
Development Plan which would improve circulation in the area and
duly approved by the competent authority, and by leaving the area
affected in the widening of such road free of cost and implement it
within one year, then higher height of the corresponding widened
road width would be considered for such sites.
(xiv) Splay at road junctions, including ‘Y’ junctions shall be provided as
follows. The area of such splay would be deemed to form part of
the road junction.
Sl.No Road Width (in m) Splay / Offset (in m)
1 Less than 12 3 X 3
2 Above 12 up to 24 4.5 X 4.5
3 Above 24 6 X 6
(xv) As per the provisions of the Andhra Pradesh Fire Service Act, 1999,
Residential buildings of height more than 18 m, Commercial
buildings of height 15m and above and buildings of public
congregation like Educational Buildings, Cinema Theatres, Function
Halls and other Assembly Buildings on plot area of 500Sq.m. and
above or of height above 6m are required to obtain prior clearance
from Andhra Pradesh State Disasters Response & Fire Services
Department from fire safety point of view.
(xvi) Stepped type buildings or incremental type buildings may be
allowed only in respect of individual residential or educational /
institutional buildings and such incremental development would be
considered only after a minimum time period of 5 years.
(xvii) For the purpose of these Rules, the following conversion from
M.K.S. and F.P.S. system shall be reckoned for the road widths
only:
(1) 3m = 10ft (2) 6m = 20ft (3) 7.5m = 25ft (4) 9m = 30ft
(5) 12m = 40ft (6) 15m = 50ft (7) 18m = 60ft (8) 24m = 80ft
(9) 30m = 100ft (10) 45m = 150ft (11) 60m = 200ft.
(xviii) All building applications for sanction of building permission for
construction of above 10m height shall be accompanied with the
following details:
(a) Report of Soil Test / Geo-technical Investigation Report issued
after personal inspection by Institution / Consultant
empanelled with / licenced by the local authority.
(b) Structural designs and drawings prepared duly taking the soil
bearing capacity into consideration and certified by qualified
Structural Engineer / Consultant Firm empanelled with / licenced
by the local authority. The Structural Engineer / Consultant Firm
is held responsible for defect in the design.
(c) Building Plan and Application shall be invariably signed by the
owner of the property, builder if any, the Architect and the
Structural Engineer who designed the structure. They shall give
their present and permanent addresses.
(d) If the construction is being taken up by a builder, an attested
copy of the registered agreement entered between the owner of
the property and the builder shall be submitted. In case of any
changes in the agreement at a later date, a copy of the same
shall also be submitted to the local authority.
(e) An undertaking on a Stamp Paper of Rs.100/-duly signed by the
owner and builder specifying that no flat or built-up area shall be
given possession to the purchaser / tenant unless they obtain the
occupancy certificate from the local authority and provide all
regular service connections.
(f) Contractor / Builders / Developer / Owner shall submit All Risks
Insurance Policy for the construction period.
```
</details>
