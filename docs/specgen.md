# Rule specs and the generator

Adding a rule unit that fits one of four templates costs one small YAML file in `rules/specs/`. From it,
`python -m app.specgen.cli build <spec>|--all` writes, deterministically:

- the rule unit (status `pilot`, `human_reviewed: false`, notes = the spec's `notes_for_reviewer`) in
  `rules/corpus/rule-units.yaml` and, when present, the corpus DB. The parent clauses are snapshotted to
  `rules/specs/clauses.yaml` so validation works without the (gitignored) database;
- a dev fixture pair `fixtures/ifc/<unit>__pass.ifc` / `__fail.ifc` (the project unit alternates mm / m by spec order);
- a held-out pair `fixtures/heldout/<unit>__heldout_pass.ifc` / `__heldout_fail.ifc` in the other project unit, with
  an exact-threshold element and a just-under one (reversed for exclusive thresholds), plus `<unit>.truth.json`, whose
  verdicts are **computed arithmetically** from the spec threshold and the generator's own element values, never by
  running a rule;
- a gold artifact from a fixed template: an IDS file in `fixtures/ids/` or a Python check in `fixtures/checks/`;
- synthetic dry-run answers in `backend/app/eval/dryrun/<unit>/` (correct, overfit, off-by-one, inverted, malformed),
  which are test data and never shown to a real model.

`validate <spec>|--all` checks specs only; `status` lists which specs are built. The evaluation harness picks every
`pilot` unit up automatically.

**Generated units are not added to any rulepack.** They are corpus and evaluation units only; a rule should enter a
rulepack only after a domain reviewer has accepted it (`docs/review/review-sheet.csv`).

## Writing a spec

```yaml
unit_id: "MBBL2016-4.8.1#1"        # <clause_id>#<suffix>; the file is rules/specs/MBBL2016-4_8_1_1.yaml
clause_id: MBBL2016-4.8.1
unit_text: The height of a store room shall be not less than 2.2 m.   # verbatim (whitespace-normalised)
topic: room height
template: space_height_min
params:
  categories: [Store]               # Pset_SpaceCommon.Category values in scope
threshold: {value: 2.2, text: "2.2", unit: m, inclusive: true}
notes_for_reviewer: >-
  Plain-English reading, every ambiguity resolved, and what part of the clause is NOT encoded.
```

The loader rejects:

- unknown fields;
- a `unit_text` that is not a substring of the parent clause;
- a threshold whose `text` does not occur in the unit or clause text as a whole number (`2.20` does not match `2.2`),
  or whose `text` is not the number in `value`;
- a unit other than `m` (widths, heights) or `m2` (areas), and a missing `inclusive`;
- door selectors the modelling profile does not define, and door operations outside `IfcDoorTypeOperationEnum`.

Write the spec file by hand: it is input, never derived from running anything.

## Templates

| Template | Tier | Checks | Gold |
|---|---|---|---|
| `door_width_min` | IDS | `IfcDoor` with the selector (`Pset_DoorCommon.FireExit = TRUE`): `Qto_DoorBaseQuantities.Width >= threshold` | IDS property facet with `minInclusive` |
| `door_operation_forbidden` | IDS | selected doors: `OperationType` not in the listed values | IDS prohibited attribute |
| `space_area_min` | geometric | `IfcSpace` with a listed Category: `space_floor_area_m2 >= threshold` (or `>`) | Python check using existing helpers only |
| `space_height_min` | geometric | same selection: `element_height_m >= threshold` (or `>`) | Python check using existing helpers only |

`door_width_min` accepts inclusive thresholds only. IDS compares unit-converted quantities and 900 mm reads as
0.9000000000000001 m, so an exclusive bound would pass a door that sits exactly on it.

**What each template guarantees** (`tests/test_specgen.py`): the generated gold is accepted by the full gate, scores
valid, dev_correct and heldout_correct, and an overfit mutation (the threshold moved off the spec value, or the
forbidden-operation list cut to what the dev pair shows) passes the dev gate but fails held-out.

**What it does not guarantee:**

- The fixtures are synthetic boxes, not real buildings.
- The generated gold is a **draft** until a person reviews the spec: it encodes the spec's reading of the clause, not
  necessarily the bye-law's intent.
- Thresholds are checked against the **text** (the number occurs), not its **meaning**: a number taken from the
  wrong sentence of the clause would still validate.
- Conditions in the clause that no template expresses (building type, room use, minimum widths of rooms) are
  dropped and recorded only in `notes_for_reviewer`.

Clauses that need anything else are listed in `docs/spec-backlog.md`.
