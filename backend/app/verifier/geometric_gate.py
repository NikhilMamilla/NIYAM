"""Geometric verifier gate: accept a generated Python check for a rule unit only if it is safe to run and its
verdicts on the unit's pass/fail fixture pair are exactly right. Stops at the first failing stage.

Generated code is only ever executed through this module (`verify_geometric`) or `sandbox.run_check` after
`validate_source`. See docs/geometric-gate.md for what the isolation does and does not guarantee."""

import ast

import ifcopenshell

from app.corpus.models import RuleUnit
from app.fixtures.builders import FixturePair
from app.geometry.helpers import validate_finding
from app.verifier import sandbox
from app.verifier.ids_gate import GateResult, _Rejected, _run_stages

STAGES = [
    "python_syntax",
    "ast_allowlist",
    "sandbox_load",
    "returns_findings",
    "applicable_on_fixtures",
    "verdict_pass_fixture",
    "verdict_fail_fixture",
    "no_unchecked_on_clean_fixtures",
]
MAX_CODE_CHARS = 8 * 1024
FORBIDDEN_NAMES = frozenset(
    "open exec eval compile __import__ getattr setattr delattr globals locals vars breakpoint input os sys "
    "subprocess socket pathlib shutil ctypes importlib builtins type dir memoryview help exit quit".split())
# str.format / format_map walk attributes (and so dunders) from a format string, which the dunder scan cannot see
FORBIDDEN_ATTRIBUTES = FORBIDDEN_NAMES | {"format", "format_map"}
FORBIDDEN_NODES = {
    ast.ClassDef: "class definitions (class)", ast.AsyncFunctionDef: "async functions", ast.Global: "global statements",
    ast.Nonlocal: "nonlocal statements", ast.Await: "await", ast.Yield: "generators", ast.YieldFrom: "generators",
    ast.Delete: "del statements", ast.With: "with statements", ast.Try: "try statements",
}


def _dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _violation(node: ast.AST, what: str) -> _Rejected:
    return _Rejected(f"line {getattr(node, 'lineno', '?')}: {what}")


def _check_syntax(code: str) -> ast.Module:
    if len(code) > MAX_CODE_CHARS:
        raise _Rejected(f"code is {len(code)} characters, longer than the {MAX_CODE_CHARS} character limit")
    try:
        return ast.parse(code)
    except SyntaxError as e:
        raise _Rejected(f"line {e.lineno}: syntax error: {e.msg}")


def _check_allowlist(tree: ast.Module) -> str:
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    for node in tree.body:
        is_docstring = isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
            and isinstance(node.value.value, str)
        is_math = isinstance(node, ast.Import) and [a.name for a in node.names] == ["math"] \
            and node.names[0].asname is None
        if isinstance(node, ast.Import) and not is_math:
            raise _violation(node, f"import {', '.join(a.name for a in node.names)} is not allowed; only 'import math'")
        if isinstance(node, ast.ImportFrom):
            raise _violation(node, "'from ... import' is not allowed; only 'import math'")
        if not (isinstance(node, ast.FunctionDef) or is_docstring or is_math):
            raise _violation(node, f"{type(node).__name__} is not allowed at top-level; only 'import math', a "
                                   "docstring and the check function are")
    if len(functions) != 1:
        raise _Rejected(f"exactly one top-level function named check is required, found {len(functions)}")
    fn = functions[0]
    if fn.name != "check":
        raise _violation(fn, f"the top-level function must be named check, not {fn.name}")
    args = fn.args
    plain = not (args.vararg or args.kwarg or args.kwonlyargs or args.defaults or args.posonlyargs)
    if [a.arg for a in args.args] != ["model", "helpers"] or not plain or fn.decorator_list:
        raise _violation(fn, "check must take exactly the parameters (model, helpers), with no defaults or decorators")

    for node in ast.walk(tree):
        if type(node) in FORBIDDEN_NODES:
            raise _violation(node, f"{FORBIDDEN_NODES[type(node)]} are not allowed")
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in tree.body:
            raise _violation(node, "imports are only allowed at the top of the file")
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or _dunder(node.id)):
            raise _violation(node, f"use of the name {node.id!r} is not allowed")
        if isinstance(node, ast.Attribute) and (node.attr in FORBIDDEN_ATTRIBUTES or _dunder(node.attr)):
            raise _violation(node, f"access to the attribute {node.attr!r} is not allowed")
    return "only import math, one check(model, helpers) function, no forbidden names"


def validate_source(code: str) -> None:
    """Stages 1-2 only. Raises ValueError with the offending construct and line (used when a rulepack is loaded)."""
    try:
        _check_allowlist(_check_syntax(code))
    except _Rejected as e:
        raise ValueError(str(e)) from e


def _labels(model, global_ids) -> list[str]:
    def one(g):
        try:
            return model.by_guid(g).Name or g
        except RuntimeError:
            return g
    return sorted(one(g) for g in global_ids)


def verify_geometric(candidate_code: str, unit: RuleUnit, fixtures: FixturePair, *,
                     timeout_s: float = sandbox.DEFAULT_TIMEOUT_S,
                     max_output_bytes: int = sandbox.DEFAULT_MAX_OUTPUT_BYTES) -> GateResult:
    state: dict = {}
    models = {"pass": ifcopenshell.open(str(fixtures.pass_path)), "fail": ifcopenshell.open(str(fixtures.fail_path))}
    paths = {"pass": fixtures.pass_path, "fail": fixtures.fail_path}

    def syntax():
        state["tree"] = _check_syntax(candidate_code)
        return f"{len(candidate_code)} characters, parses"

    def allowlist():
        return _check_allowlist(state["tree"])

    def load():
        outcome = sandbox.run_check(candidate_code, [paths["pass"], paths["fail"]], timeout_s=timeout_s,
                                    max_output_bytes=max_output_bytes)
        if not outcome.ok:
            raise _Rejected(f"the check could not run in the sandbox: {outcome.error}")
        state["raw"] = dict(zip(("pass", "fail"), outcome.results))
        return "ran on both fixtures in an isolated process"

    def returns():
        for kind, raw in state["raw"].items():
            if not isinstance(raw, list):
                raise _Rejected(f"check must return a list of findings; it returned {type(raw).__name__} "
                                f"for {paths[kind].name}")
            for i, f in enumerate(raw):
                if (problem := validate_finding(f)) is not None:
                    raise _Rejected(f"finding {i} for {paths[kind].name} is invalid: {problem}")
        state["findings"] = state["raw"]
        return f"valid findings: {', '.join(f'{k}: {len(v)}' for k, v in state['findings'].items())}"

    def of(kind, verdict):
        return {f["global_id"] for f in state["findings"][kind] if f["verdict"] == verdict}

    def applicable():
        for kind in ("pass", "fail"):
            if not (of(kind, "pass") | of(kind, "fail")):
                raise _Rejected(f"the check produced no pass or fail finding for {paths[kind].name}; "
                                "a check that decides nothing is vacuous")
        return "decides at least one element in both fixtures"

    def verdict_pass():
        bad = of("pass", "fail")
        if bad:
            raise _Rejected(f"must pass {paths['pass'].name} but failed: {_labels(models['pass'], bad)}")
        return f"no failures on {paths['pass'].name}"

    def verdict_fail():
        failed = of("fail", "fail")
        if not failed:
            raise _Rejected(f"must fail {paths['fail'].name} but passed it (check too lenient)")
        if failed != fixtures.expected_failing:
            raise _Rejected(f"failing elements {_labels(models['fail'], failed)} != expected "
                            f"{_labels(models['fail'], fixtures.expected_failing)}")
        return f"fails {paths['fail'].name} on exactly {_labels(models['fail'], failed)}"

    def no_unchecked():
        for kind in ("pass", "fail"):
            if (hiding := of(kind, "unchecked")):
                raise _Rejected(f"{paths[kind].name} has complete data but the check reported unchecked for "
                                f"{_labels(models[kind], hiding)}; a check must not hide behind unchecked")
        return "no unchecked findings on the complete fixtures"

    checks = [syntax, allowlist, load, returns, applicable, verdict_pass, verdict_fail, no_unchecked]
    return _run_stages(zip(STAGES, checks))
