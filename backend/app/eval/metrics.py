"""Evaluation metrics per model x mode, as counts and rates with Wilson 95% intervals (pure Python)."""

import math
from dataclasses import dataclass

Z95 = 1.959963984540054  # two-sided 95% normal quantile


@dataclass(frozen=True)
class Rate:
    k: int
    n: int

    @property
    def rate(self) -> float | None:
        return self.k / self.n if self.n else None

    @property
    def wilson(self) -> tuple[float, float] | None:
        return wilson_interval(self.k, self.n)

    def __str__(self) -> str:
        if not self.n:
            return f"{self.k}/0 (n/a)"
        lo, hi = self.wilson
        return f"{self.k}/{self.n} = {self.rate:.0%} [{lo:.0%}, {hi:.0%}]"


def wilson_interval(k: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """Wilson score interval for k successes in n trials; None when n == 0."""
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(max(0.0, centre - half), 12), round(min(1.0, centre + half), 12)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def group_metrics(items: list[dict]) -> dict:
    """Metrics for one model x mode. Each item has: mode, outcome, shipped, score{valid, dev_correct,
    heldout_correct, ...}, repair_rounds, total_tokens, wall_time_s."""
    n = len(items)
    scores = [i["score"] for i in items]
    shipped = [i for i in items if i["shipped"]]
    gated = bool(items) and items[0]["mode"] == "gated"
    return {
        "n": n,
        "valid": Rate(sum(s["valid"] for s in scores), n),
        "dev_correct": Rate(sum(s["dev_correct"] for s in scores), n),
        "heldout_correct": Rate(sum(s["heldout_correct"] for s in scores), n),
        "shipped": Rate(len(shipped), n),
        "wrong_shipped": Rate(sum(not i["score"]["heldout_correct"] for i in shipped), len(shipped)),
        "needs_human": Rate(sum(i["outcome"] == "needs_human" for i in items), n) if gated else None,
        "mean_repairs": _mean([i["repair_rounds"] for i in items]) if gated else None,
        "mean_tokens": _mean([i["total_tokens"] for i in items]),
        "mean_wall_s": _mean([i["wall_time_s"] for i in items]),
    }


def distinct_only(items: list[dict], duplicates: dict[str, str]) -> list[dict]:
    """The items of units that are not tagged duplicate_of another unit."""
    return [i for i in items if i["unit_id"] not in duplicates]


def correct_shipped(item: dict) -> bool:
    return item["shipped"] and item["score"]["heldout_correct"]


def paired(items: list[dict]) -> dict[str, dict[str, int]]:
    """Per model: on the same (unit, repeat), how often gated and ungated ship a held-out-correct rule."""
    by_key: dict[tuple, dict[str, dict]] = {}
    for i in items:
        by_key.setdefault((i["model"], i["unit_id"], i["repeat"]), {})[i["mode"]] = i
    table: dict[str, dict[str, int]] = {}
    for (model, _, _), modes in by_key.items():
        if {"gated", "ungated"} - modes.keys():
            continue
        g, u = correct_shipped(modes["gated"]), correct_shipped(modes["ungated"])
        row = table.setdefault(model, {"both_correct": 0, "gated_only": 0, "ungated_only": 0, "neither": 0})
        row["both_correct" if g and u else "gated_only" if g else "ungated_only" if u else "neither"] += 1
    return table


def review_share(units) -> Rate | None:
    """Share of reviewed units whose reviewer decision was modify or reject (the honest 'human edits' measure)."""
    reviewed = [u for u in units if u.human_reviewed or u.status in ("needs_rework", "rejected")]
    if not reviewed:
        return None
    return Rate(sum(u.status in ("needs_rework", "rejected") for u in reviewed), len(reviewed))
