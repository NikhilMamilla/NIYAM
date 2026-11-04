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
    assert guid("door_under_test") in result.first_failure.message


def test_cli_check_prints_stage_table(capsys):
    unit_id = "MBBL2016-5.4.2#1"
    code = cli.main(["check", unit_id, str(GOLD_DIR / f"{safe_name(unit_id)}.ids")])
    out = capsys.readouterr().out
    assert code == 0
    assert all(stage in out for stage in STAGES)
    assert "ACCEPTED" in out
