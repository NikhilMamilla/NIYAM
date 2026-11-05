"""Evaluation runs: units x modes x models x repeats, each compiled then scored on held-out fixtures."""

import hashlib
import json
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

from app.compiler.ids_compiler import build_system_prompt, compile_unit
from app.corpus.models import Clause, RuleUnit
from app.eval.scoring import score_candidate
from app.fixtures.builders import REPO_ROOT, safe_name
from app.fixtures.gold_ids import load_units
from app.llm.base import LLMError, LLMResponse, Message
from app.rulepack.loader import DEFAULT_PACK, load_rulepack

RUNS_DIR = REPO_ROOT / "eval" / "runs"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelSpec(_Strict):
    name: str
    role: Literal["hosted", "open"]


class UnitSelector(_Strict):
    status: list[Literal["pilot", "selected"]] = ["pilot"]


class Budget(_Strict):
    max_total_calls: int
    max_total_tokens: int


class EvalConfig(_Strict):
    models: list[ModelSpec]
    modes: list[Literal["gated", "ungated"]] = ["gated", "ungated"]
    units: UnitSelector = UnitSelector()
    repeats: int = 1
    temperature: float = 0.0
    max_repairs: int = 3
    budget: Budget


def load_config(path: Path) -> EvalConfig:
    return EvalConfig(**yaml.safe_load(path.read_text(encoding="utf-8")))


def select_units(config: EvalConfig) -> list[RuleUnit]:
    return [u for u in load_units().values() if u.status in config.units.status and u.tier in ("ids", "geometric")]


def worst_case_calls(config: EvalConfig, n_units: int) -> int:
    per_unit = sum(1 + config.max_repairs if m == "gated" else 1 for m in config.modes)
    return per_unit * n_units * len(config.models) * config.repeats


@dataclass
class Plan:
    units: list[RuleUnit]
    worst_calls: int
    within_budget: bool

    def lines(self, config: EvalConfig) -> list[str]:
        return [
            f"units:   {len(self.units)} ({', '.join(u.id for u in self.units)})",
            f"modes:   {', '.join(config.modes)}   models: {', '.join(m.name for m in config.models)}   "
            f"repeats: {config.repeats}",
            f"runs:    {len(self.units) * len(config.modes) * len(config.models) * config.repeats} compilations",
            f"LLM calls worst case: {self.worst_calls} (gated: 1 + {config.max_repairs} repairs per unit; ungated: 1)",
            f"budget:  max_total_calls={config.budget.max_total_calls}, max_total_tokens={config.budget.max_total_tokens}",
            "OK: within the call budget" if self.within_budget else
            "REFUSED: the worst case exceeds max_total_calls; lower repeats/units/max_repairs or raise the cap",
        ]


def make_plan(config: EvalConfig) -> Plan:
    units = select_units(config)
    calls = worst_case_calls(config, len(units))
    return Plan(units, calls, calls <= config.budget.max_total_calls)


class BudgetExceeded(LLMError):
    pass


class BudgetedProvider:
    """Counts calls and tokens across a whole run and refuses to call past the caps."""

    def __init__(self, inner, budget: Budget, counter: dict):
        self.inner, self.budget, self.counter = inner, budget, counter
        self.model = inner.model

    def complete(self, system: str, messages: list[Message], **kw) -> LLMResponse:
        if self.counter["calls"] >= self.budget.max_total_calls or \
                self.counter["tokens"] >= self.budget.max_total_tokens:
            raise BudgetExceeded(f"budget exhausted after {self.counter['calls']} calls, {self.counter['tokens']} tokens")
        response = self.inner.complete(system, messages, **kw)
        self.counter["calls"] += 1
        self.counter["tokens"] += response.input_tokens + response.output_tokens
        return response


def clause_for(unit: RuleUnit) -> Clause:
    """The parent clause, from the committed rulepack manifest (no corpus database needed)."""
    for rule in load_rulepack(DEFAULT_PACK).manifest.rules:
        if rule.unit_id == unit.id:
            return Clause(id=rule.clause_id, source_doc=rule.source_doc, clause_number=rule.clause_id.split("-", 1)[1],
                          text=rule.clause_text, page=rule.page)
    raise LookupError(f"{unit.id} is not in the rulepack manifest, so its clause text is unknown")


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True,
                               timeout=10).stdout.strip()
        return out.stdout.strip() + ("-dirty" if dirty else "") if out.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def rulepack_hash(root: Path = DEFAULT_PACK) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def run(config: EvalConfig, providers: dict[str, object], *, dry_run: bool, runs_dir: Path = RUNS_DIR,
        provider_factory=None) -> Path:
    """Compile and score every (model, mode, unit, repeat). `provider_factory(name, mode)` builds a fresh provider
    per model and mode (so modes see the same first answers); `providers` is used when it is None."""
    plan = make_plan(config)
    if not plan.within_budget:
        raise ValueError("over the call budget: " + plan.lines(config)[-1])
    started = datetime.now(timezone.utc)
    run_id = ("dryrun-" if dry_run else "") + started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    run_dir = runs_dir / run_id
    counter = {"calls": 0, "tokens": 0}
    items, stopped = [], None
    provider_classes = {}
    for spec in config.models:
        for mode in config.modes:
            inner = provider_factory(spec.name, mode) if provider_factory else providers[spec.name]
            provider_classes[spec.name] = type(inner).__name__
            provider = BudgetedProvider(inner, config.budget, counter)
            for repeat in range(config.repeats):
                for unit in plan.units:
                    if stopped:
                        break
                    attempts_dir = run_dir / "attempts" / safe_name(spec.name) / mode / f"repeat{repeat}"
                    try:
                        result = compile_unit(unit, clause_for(unit), provider, use_gate=mode == "gated",
                                              max_repairs=config.max_repairs, temperature=config.temperature,
                                              run_dir=attempts_dir)
                    except BudgetExceeded as e:
                        stopped = str(e)
                        break
                    final = result.attempts[-1].extracted_xml if result.attempts else None
                    shipped = result.outcome == "accepted" if mode == "gated" else final is not None
                    items.append({
                        "model": spec.name, "mode": mode, "unit_id": unit.id, "tier": unit.tier, "repeat": repeat,
                        "outcome": result.outcome, "shipped": shipped, "repair_rounds": result.repair_rounds,
                        "total_tokens": result.total_tokens, "wall_time_s": round(result.wall_time_s, 3),
                        "prompt_hash": result.attempts[0].prompt_hash if result.attempts else None,
                        "score": score_candidate(unit, final).to_dict(),
                    })
    meta = {
        "run_id": run_id, "date": started.isoformat(), "dry_run": dry_run, "git_commit": _git_commit(),
        "rulepack_hash": rulepack_hash(), "models": [m.model_dump() for m in config.models],
        "provider_classes": provider_classes, "modes": config.modes, "repeats": config.repeats,
        "temperature": config.temperature, "max_repairs": config.max_repairs,
        "budget": config.budget.model_dump(), "used": counter, "stopped_early": stopped,
        "system_prompt_hashes": {t: hashlib.sha256(build_system_prompt(u).encode()).hexdigest()
                                 for t, u in {u.tier: u for u in plan.units}.items()},
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "results.json").write_text(json.dumps({"meta": meta, "items": items}, indent=2), encoding="utf-8")
    return run_dir
