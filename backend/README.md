# backend

The FastAPI service (`app/`) that audits an IFC4 model against the rulepack: declared-data checks via IDS 1.0,
measured-value checks via a sandboxed Python gate, and the compiler that drafts new rules with an LLM.

Produced by hand, as ordinary Python source; `pyproject.toml` lists the dependencies.

Used by: `tests/` (pytest), `scripts/demo.ps1`/`dev-backend.sh` (runs it for the frontend and for a person), and
`scripts/check_*.py`, which import parts of it directly.
