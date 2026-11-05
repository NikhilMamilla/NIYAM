"""Score one candidate rule independently of the gate's verdict (report-only: nothing here reaches a model).

valid           all static stages pass (IDS: xml_wellformed, xsd_valid, unit_safe_bounds; geometric: python_syntax,
                ast_allowlist, sandbox_load, returns_findings)
dev_correct     accepted by the full gate on the dev pair (what the gate sees)
heldout_correct every element of both held-out models gets its hand-written verdict (boundary elements included)
vacuous         applies to nothing in any dev or held-out model
error           an exception or sandbox failure while scoring (recorded, never raised)"""

from dataclasses import asdict, dataclass, field

import ifcopenshell
from ifctester import ids

from app.corpus.models import RuleUnit
from app.fixtures import heldout
from app.fixtures.builders import fixture_pair
from app.verifier import sandbox
from app.verifier.geometric_gate import verify_geometric
from app.verifier.ids_gate import static_check, verify_ids

GEO_STATIC = ("python_syntax", "ast_allowlist", "sandbox_load", "returns_findings")
FINDING = {"pass": "pass", "fail": "fail", "unchecked": "unchecked"}


@dataclass
class CandidateScore:
    valid: bool = False
    dev_correct: bool = False
    heldout_correct: bool = False
    vacuous: bool = False
    error: str | None = None
    heldout_mismatches: list[dict] = field(default_factory=list)  # element, expected, got

    def to_dict(self) -> dict:
        return asdict(self)


def ids_verdicts(xml: str, model) -> dict[str, str]:
    """GlobalId -> pass | fail for every element any specification applies to (others are out of scope)."""
    spec_ids = ids.from_string(xml)
    spec_ids.validate(model)
    verdicts: dict[str, str] = {}
    for spec in spec_ids.specifications:
        applicable = {e.GlobalId for e in spec.applicable_entities}
        failed = applicable if spec.maxOccurs == 0 else {e.GlobalId for e in spec.failed_entities}
        for g in applicable:
            verdicts[g] = "fail" if g in failed else verdicts.get(g, "pass")
    return verdicts


def _geo_verdicts(code: str, model_paths, timeout_s: float) -> list[dict[str, str]]:
    outcome = sandbox.run_check(code, model_paths, timeout_s=timeout_s)
    if not outcome.ok:
        raise RuntimeError(f"sandbox: {outcome.error}")
    result = []
    for findings in outcome.results:
        verdicts: dict[str, str] = {}
        for f in findings:
            v = FINDING.get(f.get("verdict"), "invalid")
            if verdicts.get(f.get("global_id")) != "fail":  # the worst finding counts
                verdicts[f.get("global_id")] = v
        result.append(verdicts)
    return result


def _compare(truth: dict, per_model: dict[str, dict[str, str]]) -> list[dict]:
    mismatches = []
    for model_name, elements in truth["models"].items():
        got = per_model[model_name]
        for e in elements:
            actual = got.get(e["global_id"], "out_of_scope")
            if actual != e["expected"]:
                mismatches.append({"model": model_name, "element": e["name"], "expected": e["expected"],
                                   "got": actual})
    return mismatches


def score_candidate(unit: RuleUnit, candidate: str | None, tier: str | None = None, *,
                    heldout_root=heldout.HELDOUT_DIR, timeout_s: float = 60.0) -> CandidateScore:
    tier = tier or unit.tier
    score = CandidateScore()
    if candidate is None:
        score.error = "no candidate"
        return score
    try:
        dev = fixture_pair(unit.id)
        held = heldout.paths(unit.id, heldout_root)
        truth = heldout.load_truth(unit.id, heldout_root)
        if tier == "ids":
            score.valid = static_check(candidate).accepted
            if not score.valid:
                return score
            score.dev_correct = verify_ids(candidate, unit, dev).accepted
            per_model = {held[k].name: ids_verdicts(candidate, ifcopenshell.open(str(held[k]))) for k in ("pass", "fail")}
            dev_verdicts = [ids_verdicts(candidate, ifcopenshell.open(str(p))) for p in (dev.pass_path, dev.fail_path)]
        else:
            gate = verify_geometric(candidate, unit, dev, timeout_s=timeout_s)
            ran = {s.stage: s.passed for s in gate.stage_results}
            score.valid = all(ran.get(s) for s in GEO_STATIC)
            if not score.valid:
                return score
            score.dev_correct = gate.accepted
            names = [held["pass"].name, held["fail"].name]
            per_model = dict(zip(names, _geo_verdicts(candidate, [held["pass"], held["fail"]], timeout_s)))
            dev_verdicts = _geo_verdicts(candidate, [dev.pass_path, dev.fail_path], timeout_s)
        decided = [v for m in [*per_model.values(), *dev_verdicts] for v in m.values() if v in ("pass", "fail")]
        score.vacuous = not decided
        score.heldout_mismatches = _compare(truth, per_model)
        score.heldout_correct = not score.heldout_mismatches
    except Exception as e:  # candidates are untrusted; a scoring crash is a result, not a run failure
        score.error = f"{type(e).__name__}: {e}"[:500]
    return score
