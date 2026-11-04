# Audit engine and exports

`python -m app.audit.cli run <model.ifc> [--out <dir>]` audits a model against rulepack v0
(`rules/rulepack/v0`). No LLM and no network are involved.

## Verdicts (per rule, per element of the rule's scope class)

| Verdict | When |
|---|---|
| `out_of_scope` | the selector property is present with another value (e.g. `FireExit = FALSE`) |
| `unchecked` | the selector property is absent, or the element is selected but lacks any `required_data` item (an `OperationType` of `NOTDEFINED` counts as absent) |
| `failed` | selected, complete, and the rule's IDS fails it (for a `maxOccurs="0"` IDS: it matches) |
| `passed` | selected, complete, and the IDS passes it; never given when required data is missing |

Each element record carries `global_id`, `express_id` (its STEP id in the audited file, for
mapping to geometry in a viewer), and for failed/unchecked elements `reason_plain` (one sentence
built from the rule's IDS and the element's actual values, e.g. "Declared width is 0.9 m; this
rule requires at least 1 m.", falling back to a generic sentence plus the raw message when a value
cannot be derived) and `reason_raw` (the ifctester or engine message). Only IFC4 models are
audited; other schemas are refused.

Rule and audit status: `noncompliant` if anything failed; else `incomplete` if anything is
unchecked; else `compliant` if at least one element was checked; else `nothing_checked`.

## Summary: checks vs distinct elements

`summary` has two parts (the old flat `summary.{passed,failed,…}` was replaced; every consumer —
API, HTML, BCF, CLI, web app — was updated):

- `checks` `{passed, failed, unchecked, out_of_scope}`: one per rule × element. With three door
  rules, one door contributes three checks, so these are not door counts.
- `elements` `{total_in_model_of_scoped_classes, with_failed, with_unchecked, clean}`: distinct
  elements of the classes any rule scopes. An element with any failed check counts once under
  `with_failed`; else with any unchecked check under `with_unchecked`; the rest are `clean`.

Sample A: checks 17 / 6 / 7 / 6; 12 doors, 5 with violations, 3 not fully checked, 4 clean.

## Exports (`--out`)

- `report.json`: the full `AuditReport`.
- `report.html`: one self-contained file (inline CSS, no scripts, no external assets, all dynamic
  text HTML-escaped) with the summary and, per rule, clause text, rule text and tables of failed
  and unchecked elements.
- `issues.bcf`: BCF 2.1, one topic per failed and per unchecked element. Title
  `[<clause_id>] <short rule>`, description with the rule, element, reason and verbatim clause
  text, label `violation` or `unchecked`, priority `High` for severity `error`.

**BCF limitations:** there are no camera viewpoints and no snapshots yet. BCF 2.1 can only
reference IFC elements from a viewpoint, so each topic carries one *component-only* viewpoint
(`<Components><Selection><Component IfcGuid="…"/>`, no camera, no snapshot); the GlobalId is also
written into the description. Viewers that require a camera will open the topic without
navigating to the element.

## Geometric rules

A rule with `tier: geometric` is a Python check run through the sandbox (`docs/geometric-gate.md`), one
process per rule, in parallel, with a wall-clock timeout (`GEOMETRIC_TIMEOUT_S`, default 60 s). A rule is only
run when the model has an element of its class. Each finding is mapped onto the elements of the rule's class:
`pass` → `passed`, `fail` → `failed`, `unchecked` → `unchecked` (its sentence becomes `reason_plain`, e.g.
"Computed floor area is 1.50 m2; this rule requires at least 1.8 m2."), and an element with no finding is
`out_of_scope`. If an element has several findings the worst one counts.

If the check times out, crashes, or returns something that is not a list of valid findings, the rule has
`status: "error"` and an `error` message, no elements, and no checks. It is never reported as a pass. The overall
status is then at best `incomplete` (`summary.rules_with_errors` counts such rules), and the HTML report and the
web app say which rules could not run.
