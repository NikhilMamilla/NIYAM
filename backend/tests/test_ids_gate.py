import pytest

from app.fixtures.builders import PILOT_UNITS, FixturePair, fixture_pair, guid, safe_name
from app.fixtures.gold_ids import GOLD_DIR, load_units
from app.verifier import cli
from app.verifier.ids_gate import STAGES, verify_ids


def gold_xml(unit_id):
    return (GOLD_DIR / f"{safe_name(unit_id)}.ids").read_text(encoding="utf-8")


def gate(unit_id, xml):
    return verify_ids(xml, load_units()[unit_id], fixture_pair(unit_id))


def mutate(unit_id, old, new):
    xml = gold_xml(unit_id)
    assert old in xml, f"mutation anchor {old!r} not in gold for {unit_id}"
    return xml.replace(old, new)


@pytest.mark.parametrize("unit_id", PILOT_UNITS)
def test_gold_ids_is_accepted(unit_id):
    result = gate(unit_id, gold_xml(unit_id))
    assert result.accepted, result.first_failure
    assert [s.stage for s in result.stage_results] == STAGES
    assert all(s.passed for s in result.stage_results)
    assert result.first_failure is None


MUTATIONS = {
    "a_malformed_xml": ("MBBL2016-5.4.2#1", lambda x: x[: len(x) // 2], "xml_wellformed"),
    "b_schema_invalid": (
        "MBBL2016-5.4.2#1", lambda x: x.replace('ifcVersion="IFC4"', 'ifcVersion="IFC5"'), "xsd_valid"),
    "c_wrong_property_name": (
        "MBBL2016-5.4.1#b",
        lambda x: x.replace("<simpleValue>Width</simpleValue>", "<simpleValue>ClearWidth</simpleValue>"),
        "verdict_pass_fixture",
    ),
    "d_inverted_requirement": (
        "MBBL2016-5.4.2#1",
        lambda x: x.replace('cardinality="prohibited"', 'cardinality="required"'),
        "verdict_pass_fixture",
    ),
    "e_applicability_matches_nothing": (
        "MBBL2016-5.4.2#1",
        lambda x: x.replace("<simpleValue>IFCDOOR</simpleValue>", "<simpleValue>IFCWINDOW</simpleValue>"),
        "applicable_on_fixtures",
    ),
    "f_too_lenient": (
        "MBBL2016-5.4.1#b",
        lambda x: x.replace('<xs:minInclusive value="1.0"', '<xs:minInclusive value="0.75"'),
        "verdict_fail_fixture",
    ),
    "g_missing_fire_exit_filter": (
        "MBBL2016-5.4.1#c",
        lambda x: x[: x.index("<property dataType=\"IFCBOOLEAN\">")] + x[x.index("</property>") + len("</property>"):],
        "verdict_pass_fixture",
    ),
}


@pytest.mark.parametrize("name", MUTATIONS)
def test_mutation_is_rejected_at_expected_stage(name):
    unit_id, mutation, expected_stage = MUTATIONS[name]
    original = gold_xml(unit_id)
    mutated = mutation(original)
    assert mutated != original, "mutation did not change the XML"

    result = gate(unit_id, mutated)

    assert not result.accepted
    assert result.first_failure.stage == expected_stage, result.first_failure
    assert result.first_failure.message
    # stops at the first failure: every earlier stage passed, nothing later ran
    ran = [s.stage for s in result.stage_results]
    assert ran == STAGES[: STAGES.index(expected_stage) + 1]
    assert all(s.passed for s in result.stage_results[:-1])


def test_schema_error_text_is_surfaced():
    result = gate("MBBL2016-5.4.2#1", MUTATIONS["b_schema_invalid"][1](gold_xml("MBBL2016-5.4.2#1")))
    assert "IFC5" in result.first_failure.message


def test_fail_stage_requires_exactly_the_expected_failing_entities():
    unit_id = "MBBL2016-5.4.1#b"
    pair = fixture_pair(unit_id)
    wrong_expectation = FixturePair(pair.pass_path, pair.fail_path, frozenset({guid("control_non_exit_door")}))
    result = verify_ids(gold_xml(unit_id), load_units()[unit_id], wrong_expectation)
    assert result.first_failure.stage == "verdict_fail_fixture"
    assert "door_under_test" in result.first_failure.message  # unexpected failure, by Name
    assert "control_non_exit_door" in result.first_failure.message  # missing expected one, by Name


PROHIBITED_SPEC_5_4_2 = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <info><title>5.4.2 as a prohibited specification</title></info>
  <specifications>
    <specification name="no revolving fire exits" ifcVersion="IFC4">
      <applicability minOccurs="0" maxOccurs="0">
        <entity><name><simpleValue>IFCDOOR</simpleValue></name></entity>
        <attribute><name><simpleValue>OperationType</simpleValue></name>
          <value><simpleValue>REVOLVING</simpleValue></value></attribute>
        <property dataType="IFCBOOLEAN"><propertySet><simpleValue>Pset_DoorCommon</simpleValue></propertySet>
          <baseName><simpleValue>FireExit</simpleValue></baseName><value><simpleValue>TRUE</simpleValue></value></property>
      </applicability>
    </specification>
  </specifications>
</ids>"""


def test_both_prohibition_encodings_are_accepted():
    # gold: requirement facet with cardinality="prohibited"
    assert gate("MBBL2016-5.4.2#1", gold_xml("MBBL2016-5.4.2#1")).accepted
    # equivalent: maxOccurs="0" spec whose applicability matches nothing in the pass fixture by design
    result = gate("MBBL2016-5.4.2#1", PROHIBITED_SPEC_5_4_2)
    assert result.accepted, result.first_failure


def test_prohibited_spec_without_fire_exit_filter_is_rejected():
    # forbidding every revolving door (not only fire exits) wrongly flags the control door
    start = PROHIBITED_SPEC_5_4_2.index('<property dataType="IFCBOOLEAN">')
    end = PROHIBITED_SPEC_5_4_2.index("</property>") + len("</property>")
    xml = PROHIBITED_SPEC_5_4_2[:start] + PROHIBITED_SPEC_5_4_2[end:]
    result = gate("MBBL2016-5.4.2#1", xml)
    assert result.first_failure.stage == "verdict_pass_fixture"
    assert "control_non_exit_door" in result.first_failure.message


def test_prohibited_spec_with_typo_facet_is_still_vacuous():
    xml = PROHIBITED_SPEC_5_4_2.replace("<simpleValue>FireExit</simpleValue>", "<simpleValue>FireExitt</simpleValue>")
    result = gate("MBBL2016-5.4.2#1", xml)
    assert result.first_failure.stage == "applicable_on_fixtures"
    assert "FireExitt" in result.first_failure.message


ATTRIBUTE_BOUND_5_4_1_B = (
    "<attribute><name><simpleValue>OverallWidth</simpleValue></name><value>"
    '<xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction></value></attribute>'
)


def test_numeric_bound_on_attribute_is_rejected_as_unit_unsafe():
    xml = gold_xml("MBBL2016-5.4.1#b")
    start = xml.index('<property dataType="IFCLENGTHMEASURE"')
    end = xml.index("</property>", start) + len("</property>")
    mutated = xml[:start] + ATTRIBUTE_BOUND_5_4_1_B + xml[end:]

    result = gate("MBBL2016-5.4.1#b", mutated)

    assert result.first_failure.stage == "unit_safe_bounds"
    message = result.first_failure.message
    assert "OverallWidth" in message and "minInclusive" in message
    assert "raw file units" in message and "Qto" in message


def test_string_length_restriction_on_attribute_is_allowed():
    # xs:maxLength limits string length, not a measured value, so it is unit-safe
    xml = gold_xml("MBBL2016-5.4.1#c").replace(  # this gold declares the xs: namespace
        "</entity>",
        "</entity><attribute><name><simpleValue>Name</simpleValue></name><value>"
        '<xs:restriction base="xs:string"><xs:maxLength value="200"/></xs:restriction></value></attribute>',
        1,
    )
    result = gate("MBBL2016-5.4.1#c", xml)
    assert result.accepted, result.first_failure


def test_ifctester_runtime_error_is_a_rejection_not_a_crash():
    # schema-valid, but the regex is broken; ifctester raises while evaluating the facet
    xml = gold_xml("MBBL2016-5.4.1#c").replace(
        "</entity>",
        "</entity><attribute><name><simpleValue>Name</simpleValue></name><value>"
        '<xs:restriction base="xs:string"><xs:pattern value="door[_"/></xs:restriction></value></attribute>',
        1,
    )
    result = gate("MBBL2016-5.4.1#c", xml)
    assert result.first_failure.stage == "applicable_on_fixtures"
    assert "unterminated character class" in result.first_failure.message


def test_verdict_messages_name_entities_by_name():
    result = gate("MBBL2016-5.4.1#c", MUTATIONS["g_missing_fire_exit_filter"][1](gold_xml("MBBL2016-5.4.1#c")))
    assert "control_non_exit_door" in result.first_failure.message


def test_static_check_runs_only_the_fixture_free_stages():
    from app.verifier.ids_gate import STATIC_STAGES, static_check

    ok = static_check(gold_xml("MBBL2016-5.4.1#b"))
    assert ok.accepted and [s.stage for s in ok.stage_results] == STATIC_STAGES
    assert STATIC_STAGES == ["xml_wellformed", "xsd_valid", "unit_safe_bounds"]
    xml = gold_xml("MBBL2016-5.4.1#b")
    start = xml.index('<property dataType="IFCLENGTHMEASURE"')
    bad = static_check(xml[:start] + ATTRIBUTE_BOUND_5_4_1_B + xml[xml.index("</property>", start) + 11:])
    assert bad.first_failure.stage == "unit_safe_bounds"


def test_cli_check_prints_stage_table(capsys):
    unit_id = "MBBL2016-5.4.2#1"
    code = cli.main(["check", unit_id, str(GOLD_DIR / f"{safe_name(unit_id)}.ids")])
    out = capsys.readouterr().out
    assert code == 0
    assert all(stage in out for stage in STAGES)
    assert "ACCEPTED" in out
