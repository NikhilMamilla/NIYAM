import ifcopenshell
import pytest

from app.compiler.ids_compiler import (
    EXAMPLES_DIR,
    build_repair_message,
    build_system_prompt,
    build_user_message,
    compile_unit,
    extract_python,
)
from app.corpus.models import Clause
from app.fixtures import geo_builders as gb
from app.fixtures.builders import PILOT_UNITS, REPO_ROOT, fixture_pair, safe_name
from app.fixtures.gold_ids import load_units
from app.geometry import helpers as geo_helpers
from app.llm.scripted import ScriptedProvider
from app.verifier import geometric_gate

UNIT_ID = "MBBL2016-4.5.2#1"
CLAUSE = Clause(id="MBBL2016-4.5.2", source_doc="MBBL-2016", clause_number="4.5.2", title="Size",
                text="4.5.2 Size\nThe area of a bathroom shall not be less than 1.8 m2 with a minimum width of 1.2 m.",
                page=70, section_path=["Chapter 4"])
CHECKS = REPO_ROOT / "fixtures" / "checks"


def gold(unit_id=UNIT_ID):
    return (CHECKS / f"{safe_name(unit_id)}.py").read_text(encoding="utf-8")


def fenced(code):
    return f"Here is the check.\n```python\n{code}\n```\n"


def compile_with(responses, **kw):
    provider = ScriptedProvider(responses)
    return compile_unit(load_units()[UNIT_ID], CLAUSE, provider, **kw), provider


def test_extract_python_block():
    assert extract_python(fenced("x = 1")) == "x = 1"
    assert extract_python("```py\ny = 2\n```") == "y = 2"
    assert extract_python("no code here") is None


def test_gated_loop_accepts_a_correct_check():
    result, provider = compile_with([fenced(gold())])
    assert result.outcome == "accepted" and result.repair_rounds == 0 and len(provider.calls) == 1
    assert result.attempts[0].gate.accepted


def test_forbidden_construct_is_repaired_with_the_stage_named():
    bad = gold().replace("import math", "import os")
    result, provider = compile_with([fenced(bad), fenced(gold())])
    assert result.outcome == "accepted" and result.repair_rounds == 1
    repair = provider.calls[1]["messages"][-1].content
    assert "ast_allowlist" in repair and "import os" in repair and "```python" in repair


def test_never_valid_ends_needs_human():
    result, _ = compile_with([fenced("def check(model):\n    return []")] * 4, max_repairs=3)
    assert result.outcome == "needs_human" and result.repair_rounds == 3


def test_extraction_failure_is_fed_back():
    result, provider = compile_with(["I think the answer is 1.8", fenced(gold())])
    assert result.outcome == "accepted"
    assert "no Python code found" in provider.calls[1]["messages"][-1].content


def test_baseline_is_one_call_scored_without_repair():
    result, provider = compile_with([fenced(gold().replace("1.8", "0.5"))], use_gate=False)
    assert result.mode == "baseline" and result.outcome == "baseline_scored" and len(provider.calls) == 1
    assert not result.attempts[0].gate.accepted  # the gate only scores it


# --- the model never sees fixtures or gold checks --------------------------------------------------------------


def _distinctive_lines(text, min_len):
    return {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= min_len}


def _identifiers():
    tokens = set()
    for unit_id in [*PILOT_UNITS, *gb.UNITS]:
        for unit in ("mm", "m") if unit_id in gb.UNITS else ("mm",):
            pair = fixture_pair(unit_id, length_unit=unit)
            for path in (pair.pass_path, pair.fail_path):
                tokens.add(path.name)
                for e in ifcopenshell.open(str(path)).by_type("IfcRoot"):
                    tokens.add(e.GlobalId)
                    if e.Name and (e.is_a("IfcElement") or e.is_a("IfcSpace")):
                        tokens.add(e.Name)
    return tokens


@pytest.mark.parametrize("unit_id", gb.UNITS)
def test_geometric_prompts_contain_no_gold_check_or_fixture_content(unit_id):
    unit = load_units()[unit_id]
    clause = CLAUSE.model_copy(update={"id": unit.clause_id, "text": f"{unit.clause_id}\n{unit.text}"})
    pair = fixture_pair(unit_id)
    failures = [
        geometric_gate.verify_geometric(code, unit, pair, timeout_s=60).first_failure
        for code in (
            gold(unit_id).replace("import math", "import os"),
            "def check(model, helpers):\n    return [helpers.finding(e, 'pass', 'ok') for e in helpers.elements(model, 'IfcSpace')]\n",
        )
    ]
    prompts = [build_system_prompt(unit), build_user_message(unit, clause)]
    prompts += [build_repair_message("pass", f, pair, tier="geometric") for f in failures]
    examples = "".join(f.read_text(encoding="utf-8") for f in EXAMPLES_DIR.glob("geo_*.py"))
    forbidden = {ln for ln in _distinctive_lines(gold(unit_id), 30) if ln not in examples}
    assert any("Pset_SpaceCommon" in ln or "OccupancyType" in ln or "Computed" in ln for ln in forbidden)
    forbidden |= _distinctive_lines(pair.pass_path.read_text(), 15) | _distinctive_lines(pair.fail_path.read_text(), 15)
    forbidden |= _identifiers()
    for prompt in prompts:
        leaked = [t for t in forbidden if t in prompt]
        assert not leaked, leaked
        assert gold(unit_id) not in prompt


def test_system_prompt_is_generated_from_the_helper_module():
    system = build_system_prompt(load_units()[UNIT_ID])
    for sig in geo_helpers.signatures():
        assert f"helpers.{sig.name}{sig.signature}" in system
        assert sig.doc.splitlines()[0] in system
    assert "def check(model, helpers)" in system
    assert "NIYAM IFC modelling profile" in system and "Pset_SpaceCommon.Category" in system
    assert "```python" in system  # the output contract
    for forbidden in ("open", "getattr", "__import__"):  # the allowlist is stated to the model, from the gate's data
        assert forbidden in system


def test_ids_units_still_get_the_ids_prompt():
    system = build_system_prompt(load_units()["MBBL2016-5.4.2#1"])
    assert "IDS author" in system and "helpers." not in system
    assert build_system_prompt() == system  # the default is unchanged


def test_geometric_examples_are_valid_checks_about_other_topics():
    files = sorted(EXAMPLES_DIR.glob("geo_*.py"))
    assert 1 <= len(files) <= 2
    for f in files:
        code = f.read_text(encoding="utf-8")
        geometric_gate.validate_source(code)
        for pilot_topic in ("IfcSpace", "IfcStairFlight", "Bathroom", "Habitable", "Residential", "MBBL"):
            assert pilot_topic not in code
