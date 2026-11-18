"""Extract one real gate rejection from a local evaluation run into a small committed evidence file.

Read-only: it reads eval/runs/<run>/attempts (gitignored, local only) and rebuilds the exact repair message the model
received with the compiler's own build_repair_message (fixture names and ids masked). Writes
docs/examples/gate-rejection.json, which the website's site-data script reads.
Run from backend/ with the venv active:  python ../scripts/extract_gate_example.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.compiler.ids_compiler import build_repair_message  # noqa: E402
from app.fixtures.builders import fixture_pair, safe_name  # noqa: E402
from app.verifier.ids_gate import StageResult  # noqa: E402

RUN = "20261118T140452Z-5b7edb"
UNIT = "MBBL2016-5.4.1#b2"
MODEL_DIR = "nemotron-3-ultra-550b-a55b__NVIDIA_"
OUT = ROOT / "docs" / "examples" / "gate-rejection.json"


def main() -> int:
    path = ROOT / "eval" / "runs" / RUN / "attempts" / MODEL_DIR / "gated" / "repeat0" / \
        f"{safe_name(UNIT)}__gated__nvidia_nemotron-3-ultra-550b-a55b.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    first = record["attempts"][0]
    failure = StageResult(**first["gate"]["first_failure"])
    repair = build_repair_message(first["extracted_xml"], failure, fixture_pair(UNIT), tier="ids")
    out = {
        "run_id": RUN, "unit_id": UNIT, "model": "nemotron-3-ultra-550b-a55b (NVIDIA)", "mode": "gated", "repeat": 0,
        "attempt": 1, "outcome": record["outcome"], "repair_rounds": record["repair_rounds"],
        "stages": [{"stage": s["stage"], "passed": s["passed"]} for s in first["gate"]["stage_results"]],
        "failing_stage": failure.stage,
        "repair_message_head": repair.split("\n\nPrevious answer:")[0],
        "note": "Extracted from the local attempt log of the run; the repair message is rebuilt with the compiler's own "
                "build_repair_message, so fixture names and ids are masked exactly as the model saw them.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
