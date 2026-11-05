"""DryRunProvider: synthetic, deterministic answers that exercise the evaluation pipeline end to end.

Its answers come from the per-unit files next to this module (correct, wrong property, inverted logic, off-by-one,
overfit threshold, malformed). They are test data, never shown to a real model, and every run that uses this
provider is marked dry_run=true. Numbers from a dry run are NOT model results and must never be quoted."""

import random
import re
from pathlib import Path

from app.fixtures.builders import safe_name
from app.llm.base import LLMResponse, Message

DATA_DIR = Path(__file__).parent
UNIT_RE = re.compile(r"Rule unit (\S+):")


class DryRunProvider:
    dry_run = True

    def __init__(self, seed: str, model: str | None = None):
        self.seed = seed
        self.model = model or f"dryrun-{seed}"
        self.calls = 0
        self._last: dict[str, str] = {}  # unit -> variant answered last
        self._starts: dict[str, int] = {}  # unit -> number of fresh compilations (repeats differ)

    def _variants(self, unit_id: str) -> dict[str, Path]:
        return {p.stem: p for p in sorted((DATA_DIR / safe_name(unit_id)).glob("*.*"))}

    def complete(self, system: str, messages: list[Message], *, temperature: float, max_tokens: int) -> LLMResponse:
        self.calls += 1
        match = UNIT_RE.search(messages[0].content)
        variants = self._variants(match.group(1)) if match else {}
        if not variants:
            text = "I cannot answer that."
        else:
            unit = match.group(1)
            repairing = messages[-1].content.startswith("The verifier rejected")
            if not repairing:
                self._starts[unit] = self._starts.get(unit, 0) + 1
            # the same seed, unit, repeat and turn always give the same answer
            rng = random.Random(f"{self.seed}:{unit}:{self._starts.get(unit, 0)}:{len(messages)}")
            previous = self._last.get(unit)
            if repairing and previous == "malformed":
                name = "correct"  # a malformed answer is always fixed when the gate complains
            elif repairing and rng.random() < 0.5:
                name = "correct"
            elif repairing:
                name = previous
            else:
                names = sorted(variants)
                name = rng.choices(names, weights=[4 if n == "correct" else 1 for n in names])[0]
            self._last[unit] = name
            path = variants[name]
            fence = "xml" if path.suffix == ".ids" else "python"
            text = f"Dry-run answer ({name}).\n```{fence}\n{path.read_text(encoding='utf-8')}\n```\n"
        prompt_chars = len(system) + sum(len(m.content) for m in messages)
        return LLMResponse(text, self.model, prompt_chars // 4, len(text) // 4, latency_s=0.0)
