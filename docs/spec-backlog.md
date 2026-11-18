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
