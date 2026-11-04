import os
import re

import pytest

from app.compiler.ids_compiler import mask_fixture_details
from app.fixtures import geo_builders as gb
from app.fixtures.builders import REPO_ROOT, fixture_pair, safe_name
from app.fixtures.gold_ids import load_units
from app.verifier import geometric_gate as gate
from app.verifier import sandbox

CHECKS_DIR = REPO_ROOT / "fixtures" / "checks"
UNIT_AREA = "MBBL2016-4.5.2#1"
STAGES = gate.STAGES


def gold(unit_id):
    return (CHECKS_DIR / f"{safe_name(unit_id)}.py").read_text(encoding="utf-8")


def verify(code, unit_id=UNIT_AREA, **kw):
    kw.setdefault("timeout_s", 60.0)
    return gate.verify_geometric(code, load_units()[unit_id], fixture_pair(unit_id), **kw)


def rejected_at(result):
    assert not result.accepted
    return result.first_failure.stage


# --- gold checks are accepted (mm and m variants alike) ---------------------------------------------------------


@pytest.mark.parametrize("length_unit", ["mm", "m"])
@pytest.mark.parametrize("unit_id", gb.UNITS)
def test_gold_check_is_accepted(unit_id, length_unit):
    result = gate.verify_geometric(gold(unit_id), load_units()[unit_id], fixture_pair(unit_id, length_unit=length_unit),
                                   timeout_s=60.0)
    assert result.accepted, result.first_failure
    assert [s.stage for s in result.stage_results] == STAGES


# --- mutations are rejected at the right stage ------------------------------------------------------------------

CHECK_HEAD = "def check(model, helpers):\n"


def body(text):
    return CHECK_HEAD + "".join(f"    {line}\n" for line in text.strip().splitlines())


@pytest.mark.parametrize("code, stage, fragment", [
    ("def check(model, helpers)\n    return []\n", "python_syntax", "line 1"),
    ("x = 1\n" * 3000, "python_syntax", "longer than"),
    ("import os\n" + body("return []"), "ast_allowlist", "import os"),
    ("from math import sqrt\n" + body("return []"), "ast_allowlist", "from"),
    (body("open('x')\nreturn []"), "ast_allowlist", "open"),
    (body("return ().__class__"), "ast_allowlist", "__class__"),
    (body("return getattr(helpers, 'elements')(model, 'IfcSpace')"), "ast_allowlist", "getattr"),
    (body("return eval('[]')"), "ast_allowlist", "eval"),
    (body("return list('{0.__class__}'.format(model))"), "ast_allowlist", "format"),
    (body("return __import__('os').listdir('.')"), "ast_allowlist", "__import__"),
    (body("return []") + "\ndef other(model, helpers):\n    return []\n", "ast_allowlist", "exactly one"),
    (body("return []") + "\nPAYLOAD = 1\n", "ast_allowlist", "top-level"),
    ("def check(model):\n    return []\n", "ast_allowlist", "parameters"),
    ("def other(model, helpers):\n    return []\n", "ast_allowlist", "check"),
    (body("class X:\n    pass\nreturn []"), "ast_allowlist", "class"),
])
def test_static_mutations_are_rejected_before_anything_runs(code, stage, fragment, monkeypatch):
    monkeypatch.setattr(sandbox, "run_check", lambda *a, **k: pytest.fail("the sandbox must not be reached"))
    result = verify(code)
    assert rejected_at(result) == stage
    assert fragment in result.first_failure.message
    assert [s.stage for s in result.stage_results][-1] == stage  # stopped at the first failure


def test_ast_rejection_names_the_offending_line():
    result = verify("import math\n\n\ndef check(model, helpers):\n    x = 1\n    return open('f')\n")
    assert rejected_at(result) == "ast_allowlist" and "line 6" in result.first_failure.message


def test_infinite_loop_times_out_in_the_sandbox():
    result = verify(body("while True:\n    pass"), timeout_s=6.0)
    assert rejected_at(result) == "sandbox_load" and "timed out" in result.first_failure.message


def test_check_that_raises_is_a_sandbox_failure():
    result = verify(body("return 1 / 0"))
    assert rejected_at(result) == "sandbox_load" and "ZeroDivisionError" in result.first_failure.message


def test_secret_in_the_environment_is_not_reachable(monkeypatch):
    monkeypatch.setenv("NIYAM_TEST_API_KEY", "super-secret-value")
    # the generated code cannot even name os / the environment ...
    result = verify("import os\n" + body("return [helpers.finding(e, 'pass', os.environ['NIYAM_TEST_API_KEY'])\n"
                                         "        for e in helpers.elements(model, 'IfcSpace')]"))
    assert rejected_at(result) == "ast_allowlist" and "super-secret-value" not in result.first_failure.message
    # ... and the process it would run in never receives such a variable
    env = sandbox.scrubbed_env({**os.environ, "OPENAI_PASSWORD": "x", "my_token": "y", "SECRET_THING": "z"})
    assert not [k for k in env if re.search(r"KEY|TOKEN|SECRET|PASSWORD", k, re.I)]
    assert "super-secret-value" not in env.values()


def test_sandbox_process_sees_a_scrubbed_environment_and_a_temp_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("NIYAM_TEST_API_KEY", "super-secret-value")
    probe = sandbox.probe_environment()
    assert "NIYAM_TEST_API_KEY" not in probe["env"] and "super-secret-value" not in str(probe)
    assert probe["cwd"] != os.getcwd() and probe["isolated"] is True


@pytest.mark.parametrize("code, stage", [
    (body("return 5"), "returns_findings"),
    (body("return [{'global_id': 'x'}]"), "returns_findings"),
    (body("return [helpers.finding(e, 'maybe', 'x') for e in helpers.elements(model, 'IfcSpace')]"),
     "returns_findings"),
    # says "pass" for everything: never fails the non-compliant model
    (body("return [helpers.finding(e, 'pass', 'ok') for e in helpers.elements(model, 'IfcSpace')]"),
     "verdict_fail_fixture"),
    # says "fail" for everything: fails the compliant model
    (body("return [helpers.finding(e, 'fail', 'bad') for e in helpers.elements(model, 'IfcSpace')]"),
     "verdict_pass_fixture"),
    # hides behind unchecked everywhere
    (body("return [helpers.finding(e, 'unchecked', 'cannot tell') for e in helpers.elements(model, 'IfcSpace')]"),
     "applicable_on_fixtures"),
    (body("return []"), "applicable_on_fixtures"),
])
def test_wrong_behaviour_is_rejected_at_the_right_stage(code, stage):
    assert rejected_at(verify(code)) == stage


def test_gold_plus_a_stray_unchecked_is_rejected_as_hiding():
    code = gold(UNIT_AREA).replace(
        "    return findings\n",
        "    for space in helpers.elements(model, 'IfcSpace'):\n"
        "        if helpers.name(space) == 'control_store':\n"
        "            findings.append(helpers.finding(space, 'unchecked', 'not sure'))\n"
        "    return findings\n")
    assert rejected_at(verify(code)) == "no_unchecked_on_clean_fixtures"


def test_flagging_the_wrong_element_is_rejected():
    code = gold(UNIT_AREA).replace('category != "Bathroom"', 'category == "Bathroom"')
    assert rejected_at(verify(code)) in ("applicable_on_fixtures", "verdict_fail_fixture", "verdict_pass_fixture")


def test_output_size_is_capped():
    code = body("return [helpers.finding(e, 'pass', 'x' * 100000) for e in helpers.elements(model, 'IfcSpace')]"
                .replace("'x' * 100000", "'x'"))  # multiplication is allowed ...
    huge = body("s = 'x'\nfor i in range(25):\n    s = s + s\nreturn [helpers.finding(e, 'pass', s) "
                "for e in helpers.elements(model, 'IfcSpace')]")
    assert verify(code).first_failure.stage != "sandbox_load"
    assert rejected_at(verify(huge, max_output_bytes=100_000)) == "sandbox_load"
    assert "output" in verify(huge, max_output_bytes=100_000).first_failure.message


# --- repair prompts are masked like the IDS gate's -------------------------------------------------------------


def test_repair_prompt_from_a_geometric_failure_leaks_no_fixture_details():
    pair = fixture_pair(UNIT_AREA)
    wrong_element = body(
        "return [helpers.finding(e, 'fail' if helpers.name(e) == 'control_store' else 'pass', 'x') "
        "for e in helpers.elements(model, 'IfcSpace')]")
    for code in (wrong_element, body("return [helpers.finding(e, 'pass', 'ok') for e in helpers.elements(model, 'IfcSpace')]")):
        result = verify(code)
        assert not result.accepted
        masked = mask_fixture_details(result.first_failure.message, pair)
        for leak in (pair.pass_path.name, pair.fail_path.name, "space_under_test", "control_store", "fixtures/ifc",
                     *pair.expected_failing):
            assert leak not in masked
        assert "compliant model" in masked  # role labels, not file names
        if code is wrong_element:
            assert "a control element that must PASS" in masked  # the verdict that was wrong, not the name


def test_stage_messages_never_carry_measured_values():
    result = verify(body("return [helpers.finding(e, 'fail', 'bad 1.68') for e in helpers.elements(model, 'IfcSpace')]"))
    assert "1.68" not in result.first_failure.message
