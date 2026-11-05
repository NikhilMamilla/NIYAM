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
| 4.17.x, 5.4.3 (75, 100) | stair widths per building type, treads, risers, head-room | stairs are outside the four templates (one hand-written stair rule exists) |
| 4.24.7, 5.4.8 (79, 104) | corridor widths by building type | corridors are not an IFC class; needs the width of a footprint |
| 4.24.7.2 b, second half (80) | assembly and institutional doorways 2 m | needs the building type |
| 5.4.1 b, other sentences (100) | doorways 2 m high; bathroom, WC and store doors 0.75 m wide | door height is not a template; bathroom doors need the door-to-room relation |
| 8.x (125-127) | accessible entrances, toilets and lift doors (900 mm, etc.) | needs door-to-room or lift relations and accessibility flags |
| chapters 3 and 4 | parking, setbacks, FAR, ground coverage | counts, site geometry and ratios, not element checks |
