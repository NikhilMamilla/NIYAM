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

## Rule units, fixtures and the IDS gate

A rule unit is one verbatim sentence or sub-item of a clause (`unit-add`, `unit-list`,
`unit-show`, `unit-export` -> `rules/corpus/rule-units.yaml`). Pilot units have committed
fixture pairs in `fixtures/ifc/` and draft gold IDS in `fixtures/ids/`
(`python ../scripts/build_fixtures.py`, `python ../scripts/build_gold_ids.py`).

```bash
python -m app.verifier.cli check "MBBL2016-5.4.2#1" ../fixtures/ids/MBBL2016-5_4_2_1.ids
```

The gate accepts a candidate IDS only if it is well-formed, valid IDS 1.0, loads in ifctester,
applies to something in both fixtures, passes the `__pass` fixture and fails the `__fail`
fixture on exactly the expected element.

## IDS compiler (LLM)

Configure a hosted and/or open model in `.env` (see `.env.example`), then from `backend/`:

```bash
python -m app.compiler.cli compile "MBBL2016-5.4.2#1" --role hosted            # gated repair loop
python -m app.compiler.cli compile "MBBL2016-5.4.2#1" --role open --no-gate    # ablation baseline
python -m app.compiler.cli compile-all-pilots --role hosted --max-repairs 3
python ../scripts/live_smoke.py   # gated run of all pilots; prints "skipped" if not configured
```

The prompt contains the IDS authoring rules, `docs/modelling-profile.md` and two synthetic
examples; it never contains the pilot units' gold IDS or fixtures. Results are written to
`eval/runs/<run_id>/` (gitignored).

## Audit (no LLM)

```bash
python -m app.audit.cli run ../fixtures/samples/sample_a_mm.ifc --out ../eval/audit-demo
```

API (`uvicorn app.main:app`): `POST /api/audit` (multipart `file`, `.ifc`, max `MAX_UPLOAD_MB`),
`GET /api/audit/{id}`, `GET /api/audit/{id}/report.html`, `GET /api/audit/{id}/issues.bcf`,
`GET /api/rulepack`. Uploads are stored under `backend/data/audits/<uuid>/` (gitignored). See
`docs/audit.md` for verdicts and export limitations, and `docs/samples.md` for the synthetic models.

## Configuration

Copy `.env.example` to `.env` and fill in values. No secrets are committed.
