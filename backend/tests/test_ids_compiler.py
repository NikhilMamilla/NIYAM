import json

import ifcopenshell
import pytest
from ifctester import ids

from app.compiler import cli
from app.compiler.ids_compiler import (
    EXAMPLES_DIR,
    OUTPUT_CONTRACT,
    build_repair_message,
    build_system_prompt,
    build_user_message,
    compile_unit,
    extract_xml,
)
from app.corpus import repository as repo
from app.corpus.models import Clause
from app.fixtures.builders import PILOT_UNITS, fixture_pair, safe_name
from app.fixtures.gold_ids import GOLD_DIR, load_units
from app.llm import factory
from app.config import Settings
from app.llm.scripted import ScriptedProvider

UNIT_ID = "MBBL2016-5.4.2#1"
CLAUSE = Clause(id="MBBL2016-5.4.2", source_doc="MBBL-2016", clause_number="5.4.2", title="Revolving Doors",
                text="5.4.2 Revolving Doors\nRevolving door shall not be provided as a means of fire exit.",
                page=100, section_path=["Chapter 5", "Provisions for High-rise Development"])


def gold(unit_id=UNIT_ID):
    return (GOLD_DIR / f"{safe_name(unit_id)}.ids").read_text(encoding="utf-8")


def fenced(xml):
    return f"Here is the IDS.\n```xml\n{xml}\n```\n"


def compile_with(responses, **kw):
    provider = ScriptedProvider(responses)
    result = compile_unit(load_units()[UNIT_ID], CLAUSE, provider, **kw)
    return result, provider


# --- extraction ---------------------------------------------------------------


def test_extract_fenced_block():
    assert extract_xml(fenced("<ids>a</ids>")) == "<ids>a</ids>"


def test_extract_bare_ids_element():
    assert extract_xml('Sure: <ids xmlns="x"><info/></ids> done') == '<ids xmlns="x"><info/></ids>'


def test_extract_garbage_returns_none():
    assert extract_xml("I cannot help with that.") is None


# --- gated loop ---------------------------------------------------------------


def test_accepted_on_first_try():
    result, provider = compile_with([fenced(gold())])
    assert result.outcome == "accepted"
    assert result.repair_rounds == 0 and len(provider.calls) == 1
    assert result.attempts[0].gate.accepted
    assert (result.input_tokens, result.output_tokens, result.model) == (10, 20, "scripted")


def test_malformed_then_repaired():
    malformed = gold()[:200]
    result, provider = compile_with([fenced(malformed), fenced(gold())])

    assert result.outcome == "accepted"
    assert result.repair_rounds == 1 and len(provider.calls) == 2
    first_failure = result.attempts[0].gate.first_failure
    assert first_failure.stage == "xml_wellformed"
    repair_prompt = provider.calls[1]["messages"][-1].content
    assert first_failure.message in repair_prompt
    assert "xml_wellformed" in repair_prompt
    assert malformed in repair_prompt
    assert OUTPUT_CONTRACT in repair_prompt
    # history: original request, the bad answer, then the repair turn
    assert [m.role for m in provider.calls[1]["messages"]] == ["user", "assistant", "user"]


def test_never_valid_ends_needs_human_after_max_repairs():
    bad = fenced(gold().replace("IFCDOOR", "IFCWINDOW"))
    result, provider = compile_with([bad] * 3, max_repairs=2)
    assert result.outcome == "needs_human"
    assert len(provider.calls) == 1 + 2 and result.repair_rounds == 2
    assert all(a.gate.first_failure.stage == "applicable_on_fixtures" for a in result.attempts)


def test_extraction_failure_is_fed_back_then_recorded():
    result, provider = compile_with(["no xml here"] * 2, max_repairs=1)
    assert result.outcome == "extraction_failed"
    assert len(provider.calls) == 2
    assert "no IDS document" in provider.calls[1]["messages"][-1].content
    assert result.attempts[-1].extracted_xml is None


# --- ungated baseline ---------------------------------------------------------


def test_baseline_makes_one_call_and_scores_a_bad_candidate():
    # prohibits the wrong operation type, so the revolving door in the fail fixture slips through
    too_lenient = gold("MBBL2016-5.4.2#1").replace("<simpleValue>REVOLVING</simpleValue>",
                                                   "<simpleValue>SLIDING_TO_LEFT</simpleValue>")
    result, provider = compile_with([fenced(too_lenient), fenced(gold())], use_gate=False)
    assert len(provider.calls) == 1
    assert result.outcome == "baseline_scored" and result.repair_rounds == 0
    assert result.attempts[0].gate.accepted is False
    assert result.attempts[0].gate.first_failure.stage == "verdict_fail_fixture"


def test_baseline_scores_a_correct_candidate_as_accepted_by_gate():
    result, _ = compile_with([fenced(gold())], use_gate=False)
    assert result.outcome == "baseline_scored" and result.attempts[0].gate.accepted


def test_baseline_extraction_failure():
    result, provider = compile_with(["nothing"], use_gate=False)
    assert result.outcome == "extraction_failed" and len(provider.calls) == 1


# --- prompts never leak gold IDS or fixtures ------------------------------------


def _distinctive_lines(text, min_len):
    return {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= min_len}


@pytest.mark.parametrize("unit_id", PILOT_UNITS)
def test_prompts_contain_no_gold_ids_or_fixture_content(unit_id):
    unit = load_units()[unit_id]
    clause = CLAUSE.model_copy(update={"id": unit.clause_id, "text": f"{unit.clause_id}\n{unit.text}"})
    # a realistic repair turn: the gate's own message about a rejected candidate
    pair = fixture_pair(unit_id)
    prompts = [build_system_prompt(), build_user_message(unit, clause)]
    # the failures come from 5.4.1#c's fixtures, so they are masked with that pair, as compile_unit does
    prompts += [build_repair_message("<ids/>", f, fixture_pair("MBBL2016-5.4.1#c")) for f in _realistic_gate_failures()]
    # lines the synthetic examples share with a gold file are IDS syntax, not rule content
    examples = "".join(f.read_text(encoding="utf-8") for f in EXAMPLES_DIR.glob("*.ids"))
    forbidden = {line for line in _distinctive_lines(gold(unit_id), 30) if line not in examples}
    assert "<simpleValue>FireExit</simpleValue>" in forbidden  # the guard still covers rule content
    forbidden |= _distinctive_lines(pair.pass_path.read_text(), 15) | _distinctive_lines(pair.fail_path.read_text(), 15)
    forbidden |= _fixture_identifiers()
    for prompt in prompts:
        leaked = [token for token in forbidden if token in prompt]
        assert not leaked, leaked
        assert gold(unit_id) not in prompt


def _fixture_identifiers() -> set[str]:
    """Every fixture file name, element name and GlobalId across all pilot fixture pairs."""
    tokens = set()
    for unit_id in PILOT_UNITS:
        pair = fixture_pair(unit_id)
        for path in (pair.pass_path, pair.fail_path):
            tokens.add(path.name)
            for e in ifcopenshell.open(str(path)).by_type("IfcRoot"):
                tokens.add(e.GlobalId)
                if e.is_a("IfcElement"):
                    tokens.add(e.Name)
    return tokens


def _realistic_gate_failures():
    """Real gate failures that name fixture elements, files and GlobalIds."""
    from app.verifier.ids_gate import verify_ids
    from app.fixtures.builders import FixturePair, guid

    unit = load_units()["MBBL2016-5.4.1#c"]
    pair = fixture_pair(unit.id)
    xml = gold("MBBL2016-5.4.1#c")
    no_filter = xml[: xml.index('<property dataType="IFCBOOLEAN">')] + xml[xml.index("</property>") + 11:]
    wrong_expectation = FixturePair(pair.pass_path, pair.fail_path, frozenset({guid("control_non_exit_door")}))
    return [
        verify_ids(no_filter, unit, pair).first_failure,  # names the control door and the pass file
        verify_ids(xml, unit, wrong_expectation).first_failure,  # names both doors and the fail file
        verify_ids(xml.replace("IFCDOOR", "IFCWINDOW"), unit, pair).first_failure,  # names a file
    ]


def test_repair_prompt_masks_fixture_details_but_keeps_the_diagnosis():
    pair = fixture_pair("MBBL2016-5.4.1#c")
    over_broad, wrong_set, vacuous = _realistic_gate_failures()
    assert "control_non_exit_door" in over_broad.message  # the gate itself stays detailed

    prompt = build_repair_message("<ids/>", over_broad, pair)
    assert "verdict_pass_fixture" in prompt
    assert "must pass the compliant model but failed" in prompt
    assert "a control element that must PASS" in prompt

    prompt = build_repair_message("<ids/>", wrong_set, pair)
    assert "the element that must FAIL in the non-compliant model" in prompt
    assert "a control element that must PASS" in prompt

    prompt = build_repair_message("<ids/>", vacuous, pair)
    assert "applicable_on_fixtures" in prompt and "the compliant model" in prompt

    for p in (build_repair_message("<ids/>", f, pair) for f in (over_broad, wrong_set, vacuous)):
        assert not [t for t in _fixture_identifiers() if t in p]


def test_repair_prompt_keeps_schema_error_text():
    pair = fixture_pair(UNIT_ID)
    result, provider = compile_with([fenced(gold().replace('ifcVersion="IFC4"', 'ifcVersion="IFC5"')),
                                     fenced(gold())])
    repair = provider.calls[1]["messages"][-1].content
    assert "xsd_valid" in repair and "IFC5" in repair and "value must be one of" in repair


def test_system_prompt_carries_profile_units_caveat_and_contract():
    system = build_system_prompt()
    assert "NIYAM IFC modelling profile v0.1" in system
    assert "raw file units" in system
    assert OUTPUT_CONTRACT in system
    assert "synthetic" in system.lower()


def test_examples_are_valid_ids_and_not_about_pilot_topics():
    files = sorted(EXAMPLES_DIR.glob("*.ids"))
    assert 1 <= len(files) <= 2
    for f in files:
        ids.open(str(f), validate=True)
        text = f.read_text(encoding="utf-8").upper()
        assert "IFCDOOR" not in text and "MBBL" not in text


# --- persistence and CLI ------------------------------------------------------


def test_result_is_persisted_as_json(tmp_path):
    result, _ = compile_with([fenced(gold())], run_dir=tmp_path)
    path = tmp_path / f"{safe_name(UNIT_ID)}__gated__scripted.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["outcome"] == "accepted" and data["unit_id"] == UNIT_ID
    assert data["attempts"][0]["gate"]["accepted"] is True


def test_cli_fails_clearly_when_provider_not_configured(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(factory, "default_settings", Settings(_env_file=None))
    with pytest.raises(SystemExit) as exc:
        cli.main(["--db", str(tmp_path / "c.db"), "compile", UNIT_ID, "--role", "hosted"])
    assert "not configured" in str(exc.value)


def test_cli_compile_with_scripted_provider(monkeypatch, tmp_path, capsys):
    db = tmp_path / "c.db"
    conn = repo.connect(db)
    repo.init_db(conn)
    repo.upsert_clause(conn, CLAUSE)
    conn.close()
    monkeypatch.setattr(cli, "get_provider", lambda role: ScriptedProvider([fenced(gold())]))
    code = cli.main(["--db", str(db), "--runs-dir", str(tmp_path / "runs"), "compile", UNIT_ID, "--role", "open"])
    out = capsys.readouterr().out
    assert code == 0 and "accepted" in out
    assert len(list((tmp_path / "runs").rglob("*.json"))) == 1
