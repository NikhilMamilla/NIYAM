# NIYAM

**Status: work in progress — foundation only.**

NIYAM is an open-source tool that uses an LLM to compile Indian building rules into
[buildingSMART IDS 1.0](https://github.com/buildingSMART/IDS) specifications and Python geometric
checks, validates every draft against open-standard tools, audits IFC models, and exports BCF
issues.

Current state: an MBBL 2016 rule corpus, a verifier-gated IDS compiler and a sandbox-gated geometric (Python)
compiler, rulepack v0 (six draft, not human-reviewed rules: three door rules as IDS, three room/stair rules as
Python checks), an audit engine with HTML and BCF export, an upload API, and a web
app that shows the audit beside the model in 3D. All sample buildings are synthetic.

## Layout

- `backend/` — FastAPI app: corpus, verifier gate, LLM compiler, rulepack, audit engine, API.
- `frontend/` — Vite + React + TypeScript web app with a That Open Engine 3D viewer.
- `rules/` — rule corpus units and `rulepack/v0`; `fixtures/` — IFC fixtures, gold IDS, samples.
- `docs/` — design notes, the modelling profile, `frontend.md`, and `screenshots/`.

## Run the web app (two terminals)

```bash
# terminal 1: API on http://127.0.0.1:8000
cd backend && source .venv/Scripts/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000

# terminal 2: web app on http://localhost:5173 (proxies /api to the API)
./scripts/dev-frontend.sh            # or: cd frontend && npm ci && npm run dev
```

Open http://localhost:5173, then upload an IFC4 file or click "Try sample A (mm)". On macOS/Linux
activate the venv with `source .venv/bin/activate`. Frontend checks, from `frontend/`:
`npm test` (Vitest), `npm run build` (tsc + Vite), `npx playwright test` (starts both servers).

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
`GET /api/rulepack`, `GET /api/samples`, `GET /api/samples/{name}`, `POST /api/samples/{name}/audit`.
Only IFC4 models are audited. Uploads are stored under `backend/data/audits/<uuid>/` (gitignored). See
`docs/audit.md` for verdicts and export limitations, and `docs/samples.md` for the synthetic models.

## Geometric rules (Python checks)

Rules whose value is computed from geometry (room area, room height, stair width) are small Python functions
run only through a sandboxed gate; see `docs/geometric-gate.md` (it is defence in depth, not a hard security
boundary) and `docs/notes-geometric-spike.md`.

```bash
cd backend && source .venv/Scripts/activate
python -m app.verifier.cli check-geo "MBBL2016-4.5.2#1" ../fixtures/checks/MBBL2016-4_5_2_1.py
python -m app.rulepack.cli add "MBBL2016-4.5.2#1" ../fixtures/checks/MBBL2016-4_5_2_1.py --gate
```

## Evaluation (gated vs ungated, held-out scoring) and human review

See `docs/evaluation.md`. `python -m app.eval.cli plan | run --yes [--dry-run] | report` compiles the pilot
units per configured model with and without the gate and scores the shipped rule on held-out fixtures
(`fixtures/heldout/`, never seen by the gate or a prompt). Dry-run numbers are synthetic and must never be quoted.
Reviewers fill `docs/review/review-sheet.csv` (Excel); `python -m app.corpus.cli review-import <csv>` applies it.

## Configuration

Copy `.env.example` to `.env` and fill in values. No secrets are committed.
