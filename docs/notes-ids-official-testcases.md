# Official buildingSMART IDS test cases: a sample run (findings only)

Source: github.com/buildingSMART/IDS, branch `development`, `Documentation/ImplementersDocumentation/TestCases/`
(one folder per facet; each case is a `<pass|fail|invalid>-<name>.ids` with a `.ifc` of the same name). Licence:
**CC BY-ND 4.0, (c) buildingSMART International Ltd.** The files were downloaded to a scratch folder outside the
repository and are **not committed**; only these findings are. Checked on branch fix-mm-units with ifcopenshell /
ifctester 0.9.0.post1.

## Sample

20 cases from 4 facets: `entity` (9), `attribute` (4), `property` (3), `restriction` (4); 4 pass, 9 fail, 7 invalid.
The other folders (`classification`, `ids`, `material`, `partof`, `tolerance`) were not sampled.

The repository defines `invalid-` only as a file prefix. It is graded here as "must not pass": a fail and a rejection
both count as agreement. That reading is an assumption.

## Results

| Check | pass (4) | fail (9) | invalid (7) |
|---|---|---|---|
| ifctester result agrees with the expected one | 4 | 9 | 7 |
| NIYAM IDS static check (well-formed, IDS 1.0 XSD, unit-safe bounds) accepts the file | 3 | 9 | 7 |

ifctester agrees in all 20 cases.

The static check rejects one valid file, `restriction/pass-a_bound_can_be_inclusive_1_4.ids`, at `unit_safe_bounds`:
it bounds the attribute `RefractionIndex` between 0 and 10. That stage deliberately refuses every numeric bound on an
IFC attribute, because attribute values are compared in raw file units (a 900 mm door reads 900.0 in a millimetre
model, so `minInclusive 1.0` would pass it). For a unitless attribute such as a refraction index the rule is stricter
than the standard needs: a false positive by design, not an error. Narrowing it to length-typed attributes would need
the attribute's measure type from the schema; not done.

All 7 `invalid-` files pass the static check: they are well-formed and XSD-valid, and their invalidity (unknown
entity or attribute names, patterns on numbers, subclasses, lower-case entity names) only shows when they are run.

## Cases

`entity/`: pass-a_matching_entity_should_pass, pass-entities_can_be_specified_as_an_enumeration_1_3,
pass-inherited_predefined_types_should_pass, fail-a_null_predefined_type_should_always_fail_a_specified_predefined_types,
fail-restrictions_can_be_specified_for_the_predefined_type_3_3, fail-user_defined_types_are_checked_case_sensitively,
invalid-entities_must_be_specified_as_uppercase_strings, invalid-invalid_entities_always_fail,
invalid-subclasses_are_not_considered_as_matching. `attribute/`: fail-attributes_with_null_values_always_fail,
fail-booleans_must_be_specified_as_lowercase_strings_1_3, invalid-derived_attributes_cannot_be_checked_and_always_fail,
invalid-invalid_attribute_names_always_fail. `property/`: fail-a_logical_unknown_is_considered_false_and_will_not_pass,
fail-an_empty_string_is_considered_false_and_will_not_pass, fail-complex_properties_are_not_supported_1_2.
`restriction/`: pass-a_bound_can_be_inclusive_1_4, fail-regex_patterns_can_be_used_3_3,
invalid-patterns_always_fail_on_any_number, invalid-patterns_only_work_on_strings_and_nothing_else.

## Limits

20 of several hundred cases, chosen across facets, not at random. A specification passes when ifctester marks it
passed. NIYAM's own verdict code (`app.eval.scoring.ids_verdicts`) was not run on these files.
