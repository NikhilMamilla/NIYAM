# Deploying NIYAM

Two layers. The first is live and needs nothing from the team; the second is prepared and takes five clicks.

## Layer 1: the public site on GitHub Pages (live)

`.github/workflows/deploy-pages.yml` builds the frontend on every push to `main` and publishes it at
https://nikhilmamilla.github.io/NIYAM/ (the landing page and the dashboard at `/NIYAM/app`).

With no backend, the dashboard runs in **demo mode**: the 5 sample buildings load the results the real engine
produced (`frontend/public/demo/`, written by `scripts/build_demo_data.py`), including the verdicts, the 3D view,
the clause cards and the HTML/JSON/BCF downloads. A banner says so and the upload control is disabled with the
same explanation. `backend/tests/test_demo_data.py` re-runs the audits and fails if the saved files ever differ
from the engine's output; after changing the engine or the rulepack, run `python scripts/build_demo_data.py` from
the repository root (backend venv active) and commit `frontend/public/demo/`.

Build it locally exactly as the workflow does: `cd frontend; npm run build:pages` (output in `frontend/dist/`).
Check it with no backend: `npx playwright test -c playwright.static.config.ts`; check the live site:
`LIVE_URL=https://nikhilmamilla.github.io/NIYAM/ npx playwright test -c playwright.static.config.ts`.

## Layer 2: the API on Render, for auditing uploaded files (prepared, not deployed)

`render.yaml` describes one free Docker web service built from `backend/Dockerfile`, in public mode
(`DEPLOY_MODE=audit-only`): only `/health`, the samples, the rulepack, `/api/audit` and its report and BCF
downloads; uploads at most 20 MB and IFC only; 10 audits per minute per IP; the model is a temp file deleted after
the audit and the exports are kept in memory (the last 64 audits). No LLM, no API keys. Measured locally under a
512 MB limit: 172 MB peak after auditing all 5 samples (including the geometric ones) through the container.

1. Sign in at https://dashboard.render.com with the GitHub account that owns the repository.
2. Click **New +**, then **Blueprint**.
3. Pick the **NIYAM** repository and click **Connect**. Render reads `render.yaml` and lists `niyam-api` (free).
4. Click **Apply**. The first build takes a few minutes; wait until the service shows **Live**.
5. Copy the service URL from its page (for example `https://niyam-api.onrender.com`) and open `<URL>/health`:
   it must answer `{"status":"ok"}`.

### Point the public site at it

1. On GitHub: **Settings** → **Secrets and variables** → **Actions** → **Variables** tab → **New repository
   variable**. Name `VITE_API_URL`, value the Render URL from step 5 (no trailing slash).
2. **Actions** → **Deploy GitHub Pages** → **Run workflow** (branch `main`).

The site then checks `<VITE_API_URL>/health` on load (2 s timeout). When it answers, uploads work; when it does
not (Render's free services sleep after 15 minutes idle and take about a minute to wake), the site falls back to
demo mode by itself, so it never breaks. To go back to demo-only, delete the variable and run the workflow again.

`ALLOWED_ORIGINS` in `render.yaml` must be the origin the site is served from. It is
`https://nikhilmamilla.github.io` as long as the account's user site has no custom domain; if a custom domain is
set there, add it (comma-separated) in the service's **Environment** tab.
