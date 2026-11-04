# Geometric tier spike (MBBL 2016)

Draft notes, not human-reviewed. Searched the ingested corpus (`python -m app.corpus.cli search ...`).

## Candidates whose compared value is derived, not declared

| Clause (page) | Verbatim text (abridged) | What must be computed | Verdict |
|---|---|---|---|
| 4.5.2 (p70) | "The area of a bathroom shall not be less than 1.8 m2 with a minimum width of 1.2 m." | floor area of a space | **pilot 1** (area only) |
| 4.3.2 (p70) | "The area of habitable room shall not be less than 9.5 m2, where there is only one room with a minimum width of 2.4 m. Where there are two rooms, one ... 9.5 m2 and the other not less than 7.5 m2 ..." | floor area, plus how many habitable rooms a dwelling has | rejected: needs a per-dwelling room count and "one of these" pairing, not derivable from a plain model |
| 4.4.2 (p70) | "The area of a kitchen where separate dining area is provided, shall be not less than 5.0 m2 ..." | area, plus whether a dining area is separate | rejected: depends on a use judgement |
| 4.3.1.1 (p69) | "The height of all rooms for human habitation shall not be less than 2.75 m measured from the surface of the floor to the lowest point of the ceiling (bottom of slab) ..." | vertical extent of a space | **pilot 2** (first sentence only) |
| 4.4.1 / 4.5.1 (p70) | kitchen 2.75 m / bathroom 2.1 m height | same helper as pilot 2 | not chosen (same shape as pilot 2) |
| 4.17.2 (p75), 5.4.3c (p100) | "The minimum width of staircase shall be as follows: A Residential buildings (dwellings) 1.0 m" | stair flight width from geometry | **pilot 3** (residential row only) |
| 4.17.3 / 4.17.4.1 (p75) | tread 250 mm / riser 190 mm "limited to 12 per flight" | tread/riser of a flight | rejected: IfcStairFlight carries declared `RiserHeight`/`TreadLength` attributes, so these are declared values, an IDS job; the "per flight" count is `NumberOfRisers`, also declared |
| 4.17.4.2 (p75) | "The minimum clear head-room in any staircase shall be 2.2 m." | headroom above the walking line | rejected: needs the soffit above every tread; not computable from a flight mesh alone |
| 4.24.7 (p79), 5.4.8 (p104) | corridor widths by building type | width of a corridor space | rejected: a corridor is not an IFC class; its width is the narrow dimension of an arbitrary footprint |

## Pilot units (tier `geometric`, status `pilot`, `human_reviewed: false`)

1. `MBBL2016-4.5.2#1`: area of a bathroom ≥ 1.8 m². The "minimum width of 1.2 m" half of the sentence is not encoded.
2. `MBBL2016-4.3.1.1#1`: height of a habitable room ≥ 2.75 m. The beam, pitched-roof and air-conditioning provisions are not encoded.
3. `MBBL2016-4.17.2#A`: width of a staircase in a residential building ≥ 1.0 m.

Each unit's `notes` (in `rules/corpus/rule-units.yaml`) records its ambiguities. Selection data (modelling-profile, geometric section):
spaces carry `Pset_SpaceCommon.Category` (`Bathroom`, `Habitable`); a building's use is
`Pset_BuildingCommon.OccupancyType` (`Residential`).

## Technical spike (ifcopenshell 0.9.0.post1, Python 3.11)

Models were built with real extruded-area geometry in a millimetre and a metre project.

- **Units.** `ifcopenshell.geom.create_shape` returns coordinates in *project* units: the 1.5 × 1.2 × 2.1 m
  test space had a bounding box of 1500 × 1200 × 2100 in the mm model and 1.5 × 1.2 × 2.1 in the m model.
  Conversion to SI is therefore done once in the helper layer with `ifcopenshell.util.unit.calculate_unit_scale`
  (0.001 and 1.0).
- **(i) Floor area.** Summing the area of mesh triangles whose normal points down (−Z) gives the footprint of an
  extruded solid exactly (1 800 000 mm² = 1.8 m²). It needs no polygon library, and for a prism it equals the
  extruded footprint. A model whose space is not a prism with a flat bottom would give the area of all
  downward faces, which overstates it; the helper only claims the result for a closed mesh and returns `None`
  when it cannot be created. The declared `Qto_SpaceBaseQuantities.NetFloorArea` is read separately
  (`declared_quantity`); the helper layer does not compare them.
- **(ii) Height.** The vertical extent (max Z − min Z, world coordinates) of the space mesh gave 2100 mm / 2.1 m.
  Storey-to-storey height from `IfcBuildingStorey.Elevation` was not used: storeys can be missing elevations.
- **(iii) Stair flight width.** The mesh extent along the flight's local Y axis (local coordinates,
  `USE_WORLD_COORDS = False`) is the width by IFC convention (length along X). A flight modelled with another
  axis convention would be misread; this is a documented limit of the helper.
- **What failed/needed care.** `geometry.add_profile_representation` with a hand-made profile did not give the
  dimensions I passed in a millimetre model (extents of 4.0 and 1.1 for a 4000 × 1100 profile), so the sample
  and fixture builders create all prisms with `geometry.add_slab_representation` (a polyline footprint plus a
  depth, which behaved predictably) and the unit tests check the SI result of every fixture.
- **Dependencies.** None added. `numpy` (2.4.6) and `shapely` (2.2.0) are installed only because
  `ifcopenshell` requires them; neither is listed in `pyproject.toml`. The helpers use only the standard library
  (`math`) plus ifcopenshell, so the standard is: do not import numpy or shapely in NIYAM code.

## Standard approach

`backend/app/geometry/helpers.py`: every helper returns metres / square metres or `None` (never a guess).
Tessellate with `ifcopenshell.geom.create_shape`, convert the vertex list to SI once, then use `math`.
