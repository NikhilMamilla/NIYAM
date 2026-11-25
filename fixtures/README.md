# fixtures

Synthetic IFC4 test buildings and their expected answers: `ifc/` and `heldout/` (dev and held-out pairs per
rule), `checks/` and `ids/` (the canonical Python/IDS check for each unit), `samples/` (the five demo buildings
A-E), `invalid/` (files that should be rejected, kept for regression), `real/` (two real buildingSMART exports,
with their own licence notes).

Built by `scripts/build_fixtures.py`, `build_heldout.py`, `build_sample_buildings.py`, `build_gold_ids.py`.

Used by: backend pytest, the verifier gate, and the evaluation harness (`backend/app/eval`).
