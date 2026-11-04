# NIYAM

**Status: work in progress — foundation only.**

NIYAM is an open-source tool that uses an LLM to compile Indian building rules into
[buildingSMART IDS 1.0](https://github.com/buildingSMART/IDS) specifications and Python geometric
checks, validates every draft against open-standard tools, audits IFC models, and exports BCF
issues.

This repository currently contains only the project scaffold and a smoke test proving the core
open-source stack (IfcOpenShell + ifctester) works end to end. No LLM, rule ingestion, or frontend
code exists yet.

## Layout

- `backend/` — FastAPI app and the IFC/IDS verification logic.
- `rules/`, `fixtures/ifc/`, `fixtures/ids/`, `eval/` — placeholders for the future rule corpus,
  test models, gold IDS files, and evaluation scripts.
- `frontend/` — placeholder, not yet scaffolded.
- `docs/` — includes [`notes-ifctester.md`](docs/notes-ifctester.md), the verified ifctester API
  notes from building the smoke test.

## Setup (verified on Windows, Git Bash, Python 3.11.4)

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows cmd/PowerShell: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running the tests

```bash
cd backend
source .venv/Scripts/activate
pytest
```

## Running the API

```bash
./scripts/dev-backend.sh
```

On Windows cmd/PowerShell, or any other OS, run the equivalent manually instead:

```bash
cd backend
source .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
uvicorn app.main:app --reload
```

`GET /health` returns `{"status": "ok"}`.

## Rule corpus (MBBL 2016)

Place the source PDF at `rules/source/mbbl-2016.pdf` (see `rules/source/README.md`), then from
`backend/` with the venv active:

```bash
python -m app.corpus.cli ingest          # PDF -> backend/data/corpus.db (gitignored)
python -m app.corpus.cli stats
python -m app.corpus.cli search "stair"
python -m app.corpus.cli show MBBL2016-5.4.3
python -m app.corpus.cli mark MBBL2016-5.4.3 --tier geometric --topic stairs --status selected
python -m app.corpus.cli export-selected  # -> rules/corpus/mbbl-2016.selected.yaml (tracked)
python -m app.corpus.cli import-selected
python -m app.corpus.cli suggest          # keyword shortlist -> docs/corpus-candidates.md
```

`page` is the 1-based page of the PDF file (printed page number = PDF page - 18).

## Configuration

Copy `.env.example` to `.env` and fill in values. No secrets are committed.
