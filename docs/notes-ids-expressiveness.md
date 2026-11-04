# Can IDS 1.0 express numeric lower bounds? (ifctester 0.9.0)

Verified by `backend/tests/test_ids_expressiveness_spike.py`, which runs every case below through
`ids.open(path, validate=True)` (IDS 1.0 XSD) and `Ids.validate()` against IFC4 models with two doors
(1.2 m and 0.9 m wide), once with a metre project and once with a millimetre project.

The bound in every case is the same XML restriction:

```xml
<xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction>
```

## Results

| Requirement | metre project | millimetre project |
|---|---|---|
| attribute `IfcDoor.OverallWidth` | correct (1.2 passes, 0.9 fails) | **wrong: both pass** |
| quantity `Qto_DoorBaseQuantities.Width` (`IFCLENGTHMEASURE`) | correct | correct |
| property `NIYAM_Spike.ClearWidth` (`IfcPositiveLengthMeasure`) | correct | correct |

All three documents are valid against the IDS 1.0 XSD.

### Attribute bound: valid IDS, unsafe verdict

```xml
<attribute>
  <name><simpleValue>OverallWidth</simpleValue></name>
  <value><xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction></value>
</attribute>
```

IDS 1.0 says numeric values are in SI units. ifctester's `Property` facet converts measure values to
SI using the project units (`ifcopenshell.util.unit.convert`); its `Attribute` facet does not, and
compares the raw stored number. In a millimetre model a 900 mm door is `900.0 >= 1.0`, so it
**passes**. Most Indian BIM models are authored in millimetres, so attribute bounds would silently
accept non-compliant doors.

### Quantity bound: works in both unit systems

```xml
<property dataType="IFCLENGTHMEASURE">
  <propertySet><simpleValue>Qto_DoorBaseQuantities</simpleValue></propertySet>
  <baseName><simpleValue>Width</simpleValue></baseName>
  <value><xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction></value>
</property>
```

### Property bound (measure-typed single value): works in both unit systems

```xml
<property dataType="IFCPOSITIVELENGTHMEASURE">
  <propertySet><simpleValue>NIYAM_Spike</simpleValue></propertySet>
  <baseName><simpleValue>ClearWidth</simpleValue></baseName>
  <value><xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction></value>
</property>
```

## Two encodings of a prohibition (verified on MBBL2016-5.4.2#1)

Both are valid IDS 1.0, execute in ifctester 0.9.0 and are accepted by the gate
(`backend/tests/test_ids_gate.py::test_both_prohibition_encodings_are_accepted`).

1. Requirement facet with `cardinality="prohibited"` (the gold file):

```xml
<applicability minOccurs="0" maxOccurs="unbounded">
  <entity><name><simpleValue>IFCDOOR</simpleValue></name></entity>
  <property dataType="IFCBOOLEAN">… Pset_DoorCommon.FireExit = TRUE …</property>
</applicability>
<requirements>
  <attribute cardinality="prohibited">
    <name><simpleValue>OperationType</simpleValue></name>
    <value><simpleValue>REVOLVING</simpleValue></value>
  </attribute>
</requirements>
```

2. Prohibited specification, `maxOccurs="0"`, no `<requirements>` (the violation is the applicability):

```xml
<applicability minOccurs="0" maxOccurs="0">
  <entity><name><simpleValue>IFCDOOR</simpleValue></name></entity>
  <attribute><name><simpleValue>OperationType</simpleValue></name>
    <value><simpleValue>REVOLVING</simpleValue></value></attribute>
  <property dataType="IFCBOOLEAN">… Pset_DoorCommon.FireExit = TRUE …</property>
</applicability>
```

Differences that matter for the gate:

- For a `maxOccurs="0"` spec, ifctester sets `status = False` when anything is applicable but
  leaves `failed_entities` empty. The gate therefore treats every applicable entity of a
  prohibited spec as a failing entity when comparing against the expected set.
- Its full applicability matches nothing in a compliant model by design, so the gate's vacuity
  check is per facet: every applicability facet must match at least one entity in both fixtures on
  its own (catches misspelt classes/properties), and only non-prohibited specs must additionally
  match as a whole.
- Facet order inside `<applicability>` is fixed by the XSD: entity, partOf, classification,
  attribute, property, material.

## Consequences for tiering

- A numeric bound is IDS-tier only if the value lives in a **quantity or measure-typed property**
  that the model actually carries (e.g. `Qto_DoorBaseQuantities.Width`). Gold IDS must not bound
  IFC attributes such as `OverallWidth` / `OverallHeight`.
- IDS checks only what the model *declares*. Nothing ties `Qto_DoorBaseQuantities.Width` to the
  real geometry, and IFC/IDS do not define which width (clear opening, leaf, overall) it means.
  Rules about *measured* geometry (clear widths, stair rise/going, distances, setbacks, travel
  distance, headroom) need the **geometric** tier.
- Elements without a suitable quantity or property (e.g. `IfcStair` has no width attribute or
  standard width quantity) cannot be bounded in IDS at all → geometric tier.
- Not tested here: upper bounds (`maxInclusive`) and exclusive bounds behave the same way in
  ifctester's code (`Restriction.__eq__`), but were not run. Area/volume units not tested.
