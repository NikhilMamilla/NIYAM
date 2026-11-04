# NIYAM IFC modelling profile v0.1

NIYAM compiles building rules into IDS against this profile. A rule can only be checked on a model
that follows it. The profile covers exactly what the current rules use; nothing else is defined yet.

## General

- Schema: IFC4. IDS specifications target `ifcVersion="IFC4"`.
- Project length unit: millimetre or metre (`IfcSIUnit` LENGTHUNIT with prefix MILLI or none),
  declared in the project's `IfcUnitAssignment`.
- Numeric values in IDS are written in SI units (metres). Quantities and measure-typed properties
  are converted from the project unit to SI before comparison; IFC attributes are not. Numeric
  bounds must therefore be placed on quantities or measure-typed properties, never on attributes.

## Doors (`IfcDoor` occurrences)

| Meaning | Where it is read | Type / values |
|---|---|---|
| Door is an exit door (a means of fire exit / exit doorway) | `Pset_DoorCommon.FireExit` | `IfcBoolean`; `TRUE` = exit door, `FALSE` = not an exit door |
| Door width | `Qto_DoorBaseQuantities.Width` | `IfcQuantityLength` in the project length unit |
| Door operation (swing, sliding, revolving, ...) | attribute `IfcDoor.OperationType` | `IfcDoorTypeOperationEnum`, e.g. `SINGLE_SWING_LEFT`, `SLIDING_TO_LEFT`, `DOUBLE_DOOR_SLIDING`, `ROLLINGUP`, `REVOLVING` |

- Exit-door rules select doors with `Pset_DoorCommon.FireExit = TRUE`; doors with `FALSE` are out of
  scope of those rules.
- `OperationType` is read from the door occurrence itself, not from an `IfcDoorType`.
- An `IfcDoor.OperationType` of `NOTDEFINED` (or no value) counts as missing data: rules that need the
  operation type report the door as unchecked.
- The profile does not define which physical width `Qto_DoorBaseQuantities.Width` represents
  (clear opening, leaf or frame). Rules compare the declared quantity only.

## Missing data is "unchecked", never "pass"

An element that a rule should apply to but that lacks the profile data the rule needs (for example
a door without `Pset_DoorCommon.FireExit`, or an exit door without `Qto_DoorBaseQuantities.Width`)
cannot be checked. Audits must report such elements as **unchecked**, not as passing. An IDS
specification that applies to nothing in a model proves nothing about that model.
