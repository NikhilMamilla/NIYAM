# Spec backlog: clauses that do not fit the four templates

Searched: the chapter 4 space and height requirements (4.3 to 4.13), the exit-door clauses (4.24.7.2, 5.4.1,
5.4.2), the stair and corridor clauses, the accessibility chapter (8.x) and `docs/corpus-candidates.md`, with direct
corpus searches ("height", "area", "door", "clear opening", "headroom"). Nothing below is encoded in this phase.

| Clause (page) | Text (abridged) | Why it is not a T1-T4 unit |
|---|---|---|
| 4.3.2 (70) | habitable room 9.5 m2 "where there is only one room"; 7.5 m2 for the second of two rooms | depends on the number of habitable rooms per dwelling |
| 4.4.2 (70) | kitchen 5.0 m2 "where separate dining area is provided", 4.5 m2 with a separate store, 7.5 m2 if also a dining area | three thresholds chosen by how the kitchen is used; any single one is wrong for the others |
| 4.3.1.1, rest (69) | 2.4 m under beams; average height for pitched roofs; 2.4 m in air-conditioned rooms | needs beam or roof geometry, or an air-conditioning flag |
| 4.3.1.2 (70) | educational and industrial ceiling heights (3.6 m / 3 m) | depends on building type and climate region |
| 4.4.2, 4.5.2, 4.13 widths | "with a minimum width of ..." | the width of a non-rectangular room is not defined and there is no helper |
| 4.6.1 (71) | loft head-room 2.2 m; loft at most 1.5 m high | head-room under a loft needs loft and room geometry together; a maximum is not a template |
| 4.6.2 (71) | loft not more than 25 percent of the floor area | a ratio between two elements |
| 4.7.2, second sentence (71) | mezzanine area at most one-third of the plinth area | a ratio to the building's plinth area |
| 4.9.2 (72) | private garage 3.0 m x 6.0 m | two dimensions of a room; no helper |
| 4.10.4 c (72) | basement ceiling 0.9 m to 1.2 m above average ground level | needs the surrounding ground level |
| 4.13, rest (73) | 0.75 m passages, 18.5 m travel distance, 2.2 m maximum height of unventilated cabins | passages, distances, and a maximum with a lighting condition |
| 4.17.x, 5.4.3 (75, 100) | stair widths per building type, treads, risers, head-room | stairs are outside the templates (one hand-written stair rule exists) |
| 4.24.7, 5.4.8 (79, 104) | corridor widths by building type | corridors are not an IFC class; needs the width of a footprint |
| 4.24.7.2 b, second half (80) | assembly and institutional doorways 2 m | needs the building type |
| 5.4.1 b, third sentence (100) | bathroom, WC and store doors 0.75 m wide | the doors are identified by the room they serve (no door-to-room relation); the 2 m doorway height is now unit 5.4.1#b2 |
| 8.x (125-127) | accessible entrances, toilets and lift doors (900 mm, etc.) | needs door-to-room or lift relations and accessibility flags |
| chapters 3 and 4 | parking, setbacks, FAR, ground coverage | counts, site geometry and ratios, not element checks |
| 3.4.5, 3.4.6 (54) | low-income housing: first room 9 sqm, other 6.5 / 7.5 sqm, total 15.5 sqm | depends on the number and order of rooms per dwelling |
| 4.2.1.1 (69) | plinth at least 450 mm above surrounding ground | needs the ground level |
| 4.5.3 d, f (71) | wall finish to 1 m; window of at least 0.3 m2 | finishes and openings are not templates |
| 4.12 (73) | parapets and handrails 1.0 m to 1.2 m high | a range on railings; no railing template |
| 4.17.2 rows, 5.4.3 c, 8.5 (75, 100, 125) | stair widths 1.0 to 2.0 m, 1350 mm accessible stair | every row depends on building type or on which stair serves the disabled, so a `stair_width_min` template would only encode conditional rows; not added |
| 4.33.6, 8.4.1, 8.7.x (87, 125-127) | door clear openings 900 / 780 mm | clear opening is not the modelled width, and the doors are identified by the room they serve |
| 5.4.8 c (104) | corridors 2.4 m high where stairways discharge through them | conditional on stair discharge |
| 7.2 (119) | 3.0 m clear height under balconies or girders; 2.75 m head room under beams | needs beam geometry |
| 11.9.2 b (144) | fire lift floor area 1.4 sq m | a lift car is not an IfcSpace |
| 11.29 j, 4.24.7.1 (157, 79) | aisle and ramp widths | no aisle or ramp template |

## AI second-opinion review findings, not previously disclosed (docs/review/ai-review-summary.md)

ChatGPT's second-opinion review (`docs/review/ai-review-chatgpt-2026-11-25.csv`) raised three points our own
machine_reading had not written down. None change the spec, fixtures or truth files; they are future work for
whoever reviews these units next.

| Unit | What the reviewer found |
|---|---|
| MBBL2016-7.1#1 | 4.5 m workroom height excludes "room intended for storage, godowns and the like purposes", and the Authority may allow 3.66 m for a qualifying small factory (under 50 workers, flatted-factory/service-industry class); neither exclusion is encoded or disclosed |
| MBBL2016-4.24.7.2#b | Listed as a duplicate of MBBL2016-5.4.1#b, but it is not a pure duplicate: it carries a 2 m exit-doorway width exception for assembly and institutional buildings that 5.4.1#b's wording lacks |
| MBBL2016-4.5.1#1 | The clause measures "to the lowest point in the ceiling"; the current check uses the space's overall vertical extent, which can overstate height where the ceiling is sloped or has a lower portion |

## Reading-dependent units (found in evaluation run 20261118T140452Z-5b7edb)

These units are encoded, but their spec reading departs from the literal clause text. They are listed first in the
review sheet (`reading_dependent` column). Their status and truth files are unchanged until a reviewer decides.

| Unit | Literal text | Spec reading | What the run showed |
|---|---|---|---|
| 4.8.2#1 | store room 3 m2 "where provided in a residential building" | every store room, any building type | all 12 final candidates (both models, both modes, 3 repeats) kept the residential condition; the test buildings declare no OccupancyType, so the rule never applied (gate: applicable_on_fixtures) |
| 5.4.1#b2 | "Doorways shall be not less than 2 m in height" | exit doors only (FireExit = TRUE) | the large model's 6 final candidates checked every IfcDoor and failed the compliant test building, which has a lower non-exit door (gate: verdict_pass_fixture); the small model's 6 all used FireExit |

The report's POST-HOC sensitivity table shows the headline numbers without these two units. It was added after
seeing the results and is not a pre-registered analysis.

## Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied)

Searched every page outside the locality lists (pages 1-30 and 280-373) for doors, rooms, heights and areas. The rules
defer room sizes to the NBC: Rule 15(a)(vi), "the requirements of parts of the building like size and area requirements
of habitable rooms, kitchen, bathrooms and Water closets ... shall conform to the National Building Code of India".
A second, full-text read of Rules 5, 7 and 13 (applying the MBBL standard: conditions in headings or other sentences are dropped and written into the notes) gave two units: `TGBR2012-5#c` (stilt floor height at least 2.5m) and `TGBR2012-5#fxi` (chowk / courtyard area at least 9sq.m). The rows below are what remains rejected.

| Clause (page) | Text (verbatim or abridged) | Why it is not a unit |
|---|---|---|
| TGBR2012-5 (10) | parking floors "where mechanical system and lift are provided": not less than 4.5m | the condition is in the same sentence; a Category for it would bake the condition into a name |
| TGBR2012-13 (19) | cellar ventilation not less than 2.5% of each cellar floor area | a ratio |
| TGBR2012-7 (14) | chowk / inner courtyard at least 25 sq.m, no side less than 3m (high-rise) | it differs from TGBR2012-5#fxi only by its heading; with the heading dropped it would fail every non-high-rise chowk of 9-25 sq.m, while the 9 sq.m unit holds for all buildings |
| TGBR2012-13 (19) | watchman room and toilets in a stilt floor, maximum 25 sq.m | a maximum; conditional on a stilt floor |
| TGBR2012-AnnexureIII (284) | "clear height of 2100 MM in the passage/escape path" | fire provisions for vertical openings; a passage, not a room |
| TGBR2012-AnnexureIV (296, 298, 305) | egress height 2.4 m, door clear widths 2.0 / 1.2 m, a room of at least 9 m2 | the annexure's 'Building' means a hospital above 30 m: building type and height |
| TGBR2012-AnnexureV (315, 318) | door clear width 900 mm; WC door 800 mm | accessibility clear openings and doors identified by the room they serve (as for MBBL 8.x) |

Same topic, different numbers (verbatim):

| Topic | MBBL 2016 | Telangana 2012 |
|---|---|---|
| high-rise threshold | MBBL2016-1.1 (p19): "A building above 4 stories, and/or a building exceeding 15 meters or more in height (without stilt) and 17.5M (including stilt)." | TGBR2012-5 (p9): "NON-HIGH RISE BUILDINGS (Buildings below 18m in height inclusive of Stilt / Parking Floor)" |
| stilt floor height | MBBL2016-5.5.11 (p108): "Stilts in high-rise will not be restricted to height of 2.4m as long as it is used for parking." | TGBR2012-5 (p10): "Height of stilt floor shall not be less than 2.5m." |
