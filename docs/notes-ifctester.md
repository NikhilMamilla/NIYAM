# ifctester notes (verified against 0.9.0)

- IDS building: `ids.Ids()` + `ids.Specification(...)`, append `ids.Entity(name="IFCDOOR")` to
  `spec.applicability` and `ids.Property(propertySet=..., baseName=..., cardinality="required")`
  to `spec.requirements`.
- XSD validation happens on read, not write: `spec_ids.to_xml(path)` does not raise on an invalid
  spec. Use `ids.open(path, validate=True)` (raises `ids.IdsXmlValidationError` on schema failure).
- Validation: `spec_ids.validate(ifc_file, filepath=...)`, then read
  `spec.status`, `spec.passed_entities`, `spec.failed_entities` (sets of
  `ifcopenshell.entity_instance`).
- Reporters (`ifctester.reporter`) all need `.report()` called before `.to_file(path)` — `report()`
  populates `self.results`, which `to_file` just serializes/renders.
- `reporter.Bcf` works out of the box (`bcf-client` is pulled in automatically as an ifctester
  dependency) but its `to_file` calls `BcfXml.save_project`, which is deprecated upstream in favor
  of `.save()`. It still works and produces a non-empty `.bcfzip`; flagged here in case a future
  `ifctester`/`bcf-client` release removes `save_project` and this needs updating to `.save()`.
