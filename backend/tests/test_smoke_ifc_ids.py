import json

import ifcopenshell
import ifcopenshell.api
import pytest
from ifctester import ids, reporter


def build_ifc_model(tmp_path):
    f = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcProject", name="NIYAM Smoke Project")
    site = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Building")
    storey = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name="Storey")

    ifcopenshell.api.run("aggregate.assign_object", f, products=[site], relating_object=project)
    ifcopenshell.api.run("aggregate.assign_object", f, products=[building], relating_object=site)
    ifcopenshell.api.run("aggregate.assign_object", f, products=[storey], relating_object=building)

    door_a = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcDoor", name="Door A")
    door_b = ifcopenshell.api.run("root.create_entity", f, ifc_class="IfcDoor", name="Door B")
    ifcopenshell.api.run("spatial.assign_container", f, products=[door_a, door_b], relating_structure=storey)

    pset_a = ifcopenshell.api.run("pset.add_pset", f, product=door_a, name="Pset_DoorCommon")
    ifcopenshell.api.run("pset.edit_pset", f, pset=pset_a, properties={"FireRating": "FD60"})

    ifc_path = tmp_path / "model.ifc"
    f.write(str(ifc_path))
    return f, door_a, door_b, ifc_path


def build_ids_spec():
    spec = ids.Specification(name="Doors must declare a fire rating", minOccurs=1, ifcVersion=["IFC4"])
    spec.applicability.append(ids.Entity(name="IFCDOOR"))
    spec.requirements.append(
        ids.Property(propertySet="Pset_DoorCommon", baseName="FireRating", cardinality="required")
    )

    spec_ids = ids.Ids(title="NIYAM smoke test IDS")
    spec_ids.specifications.append(spec)
    return spec_ids


def test_ids_xml_round_trips_and_validates_against_xsd(tmp_path):
    spec_ids = build_ids_spec()
    xml_path = tmp_path / "spec.ids.xml"
    spec_ids.to_xml(str(xml_path))

    reopened = ids.open(str(xml_path), validate=True)
    assert reopened.specifications[0].name == "Doors must declare a fire rating"


def test_malformed_ids_fails_xsd_validation(tmp_path):
    malformed_path = tmp_path / "malformed.ids.xml"
    malformed_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ids xmlns="http://standards.buildingsmart.org/IDS">'
        "<specifications><specification name=\"Broken\"></specification></specifications>"
        "</ids>",
        encoding="utf-8",
    )
    with pytest.raises(ids.IdsXmlValidationError):
        ids.open(str(malformed_path), validate=True)


def test_ids_validates_ifc_model_and_identifies_passing_and_failing_doors(tmp_path):
    f, door_a, door_b, ifc_path = build_ifc_model(tmp_path)
    spec_ids = build_ids_spec()

    spec_ids.validate(f, filepath=str(ifc_path))
    spec = spec_ids.specifications[0]

    assert spec.status is False
    assert door_a in spec.passed_entities
    assert door_b in spec.failed_entities


def test_json_and_html_reports_are_written_and_non_empty(tmp_path):
    f, door_a, door_b, ifc_path = build_ifc_model(tmp_path)
    spec_ids = build_ids_spec()
    spec_ids.validate(f, filepath=str(ifc_path))

    json_path = tmp_path / "report.json"
    json_reporter = reporter.Json(spec_ids)
    json_reporter.report()
    json_reporter.to_file(str(json_path))
    assert json_path.stat().st_size > 0
    with open(json_path, encoding="utf-8") as fh:
        payload = json.load(fh)
    assert payload["status"] is False

    html_path = tmp_path / "report.html"
    html_reporter = reporter.Html(spec_ids)
    html_reporter.report()
    html_reporter.to_file(str(html_path))
    assert html_path.stat().st_size > 0


def test_bcf_report_is_produced_for_failures(tmp_path):
    f, door_a, door_b, ifc_path = build_ifc_model(tmp_path)
    spec_ids = build_ids_spec()
    spec_ids.validate(f, filepath=str(ifc_path))

    bcf_path = tmp_path / "report.bcfzip"
    bcf_reporter = reporter.Bcf(spec_ids)
    bcf_reporter.report()
    bcf_reporter.to_file(str(bcf_path))
    assert bcf_path.exists()
    assert bcf_path.stat().st_size > 0
