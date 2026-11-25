# scripts

Build and check scripts run from the repository root: `check_numbers.py`/`check_images.py`/`check_public_ready.py`
(the project's own correctness gates), the fixture/sample/figure builders, `rescore_after_mm_fix.py`, the BCF
validator, and `demo.ps1`/`demo.sh`/`dev-backend.sh`/`dev-frontend.sh` (run the app for a person).

Plain Python/PowerShell/shell, run directly (`python scripts/check_numbers.py`, `.\scripts\demo.ps1`).

Used by: whoever is verifying a claim or running the demo; `STATUS.md`'s "Reproduce" section lists the exact
commands.
