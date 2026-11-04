"""Characterises what ifctester 0.9.0 does with numeric lower bounds in IDS 1.0.
Findings are written up in docs/notes-ids-expressiveness.md; if this test starts failing after an
ifctester upgrade, the behaviour changed and that note must be updated."""

import ifcopenshell
import ifcopenshell.api
import pytest
from ifctester import ids

MIN_1_0 = '<xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction>'

REQUIREMENTS = {
    "attribute IfcDoor.OverallWidth": (
        f"<attribute><name><simpleValue>OverallWidth</simpleValue></name><value>{MIN_1_0}</value></attribute>"
    ),
    "quantity Qto_DoorBaseQuantities.Width": (
        '<property dataType="IFCLENGTHMEASURE"><propertySet><simpleValue>Qto_DoorBaseQuantities</simpleValue>'
        f"</propertySet><baseName><simpleValue>Width</simpleValue></baseName><value>{MIN_1_0}</value></property>"
    ),
    "property NIYAM_Spike.ClearWidth (IfcPositiveLengthMeasure)": (
        '<property dataType="IFCPOSITIVELENGTHMEASURE"><propertySet><simpleValue>NIYAM_Spike</simpleValue>'
        f"</propertySet><baseName><simpleValue>ClearWidth</simpleValue></baseName><value>{MIN_1_0}</value></property>"
    ),
}


def ids_document(requirement: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<ids xmlns="http://standards.buildingsmart.org/IDS" xmlns:xs="http://www.w3.org/2001/XMLSchema">'
        "<info><title>spike</title></info><specifications>"
        '<specification name="width lower bound" ifcVersion="IFC4"><applicability>'
        "<entity><name><simpleValue>IFCDOOR</simpleValue></name></entity></applicability>"
        f"<requirements>{requirement}</requirements></specification></specifications></ids>"
    )


def door_model(length_prefix: str | None, widths: list[float]):
    f = ifcopenshell.file(schema="IFC4")
    ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcProject")
    unit = ifcopenshell.api.run("unit.add_si_unit", f, unit_type="LENGTHUNIT", prefix=length_prefix)
    ifcopenshell.api.run("unit.assign_unit", f, units=[unit])
    for w in widths:
        door = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcDoor", name=str(w))
        door.OverallWidth = w
        qto = ifcopenshell.api.run("pset.add_qto", f, product=door, name="Qto_DoorBaseQuantities")
        ifcopenshell.api.run("pset.edit_qto", f, qto=qto, properties={"Width": w})
        pset = ifcopenshell.api.run("pset.add_pset", f, product=door, name="NIYAM_Spike")
        ifcopenshell.api.run("pset.edit_pset", f, pset=pset,
                             properties={"ClearWidth": f.createIfcPositiveLengthMeasure(w)})
    return f


# (requirement, project length unit, door widths in project units) -> which doors pass
CASES = [
    ("attribute IfcDoor.OverallWidth", None, [1.2, 0.9], {"1.2"}),
    ("attribute IfcDoor.OverallWidth", "MILLI", [1200.0, 900.0], {"1200.0", "900.0"}),  # WRONG: no unit conversion
    ("quantity Qto_DoorBaseQuantities.Width", None, [1.2, 0.9], {"1.2"}),
    ("quantity Qto_DoorBaseQuantities.Width", "MILLI", [1200.0, 900.0], {"1200.0"}),
    ("property NIYAM_Spike.ClearWidth (IfcPositiveLengthMeasure)", None, [1.2, 0.9], {"1.2"}),
    ("property NIYAM_Spike.ClearWidth (IfcPositiveLengthMeasure)", "MILLI", [1200.0, 900.0], {"1200.0"}),
]


@pytest.mark.parametrize("requirement, prefix, widths, expected_passing", CASES)
def test_numeric_lower_bound(tmp_path, requirement, prefix, widths, expected_passing):
    path = tmp_path / "spike.ids"
    path.write_text(ids_document(REQUIREMENTS[requirement]), encoding="utf-8")
    spec_ids = ids.open(str(path), validate=True)  # the exact XML is valid IDS 1.0

    spec_ids.validate(door_model(prefix, widths))

    [spec] = spec_ids.specifications
    assert len(spec.applicable_entities) == 2
    assert {d.Name for d in spec.passed_entities} == expected_passing
