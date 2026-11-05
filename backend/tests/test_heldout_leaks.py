"""Held-out fixtures must never reach a model: no file name, element name, GlobalId or content in any prompt."""

from pathlib import Path

import ifcopenshell
import pytest

from app.compiler import ids_compiler
from app.compiler.ids_compiler import build_repair_message, build_system_prompt, build_user_message
from app.corpus.models import Clause
from app.fixtures import heldout
from app.fixtures.builders import fixture_pair
from app.fixtures.gold_ids import load_units
from app.verifier.ids_gate import StageResult


def heldout_tokens() -> set[str]:
    tokens = set()
    for unit_id in heldout.UNITS:
        p = heldout.paths(unit_id)
        tokens |= {p["pass"].name, p["fail"].name, p["truth"].name, "heldout"}
        for key in ("pass", "fail"):
            text = p[key].read_text()
            tokens |= {ln.strip() for ln in text.splitlines() if len(ln.strip()) >= 15 and ln.startswith("#")}
            for e in ifcopenshell.open(str(p[key])).by_type("IfcRoot"):
                tokens.add(e.GlobalId)
                if e.Name and e.Name.startswith("HO "):
                    tokens.add(e.Name)
    return tokens


TOKENS = heldout_tokens()


def leaks(prompt: str) -> list[str]:
    return [t for t in TOKENS if t in prompt]


def prompts_for(unit_id: str) -> list[str]:
    unit = load_units()[unit_id]
    clause = Clause(id=unit.clause_id, source_doc="MBBL-2016", clause_number="x", text=unit.text, page=1)
    failures = [StageResult("verdict_fail_fixture", False, "must fail the non-compliant model but passed it"),
                StageResult("ast_allowlist", False, "line 1: import os is not allowed; only 'import math'")]
    return [build_system_prompt(unit), build_system_prompt(), build_user_message(unit, clause),
            *(build_repair_message("candidate", f, fixture_pair(unit_id), tier=unit.tier) for f in failures)]


@pytest.mark.parametrize("unit_id", heldout.UNITS)
def test_no_heldout_detail_in_any_compiler_prompt(unit_id):
    assert len(TOKENS) > 50  # the guard covers real content: names, ids, entity lines, file names
    for prompt in prompts_for(unit_id):
        assert not leaks(prompt), leaks(prompt)


def test_the_guard_fails_when_a_heldout_name_is_injected():
    prompt = prompts_for("MBBL2016-5.4.1#b")[0]
    assert leaks(prompt + "\nExample element: HO exit 0.99 m") == ["HO exit 0.99 m"]
    assert leaks(prompt + heldout.paths("MBBL2016-4.5.2#1")["fail"].name)


def test_compiler_code_never_refers_to_heldout_fixtures():
    for path in Path(ids_compiler.__file__).parent.rglob("*.py"):
        assert "heldout" not in path.read_text(encoding="utf-8").lower(), path
