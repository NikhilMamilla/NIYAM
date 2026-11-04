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

Rule and audit status: `noncompliant` if anything failed; else `incomplete` if anything is
unchecked; else `compliant` if at least one element was checked; else `nothing_checked`.

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
