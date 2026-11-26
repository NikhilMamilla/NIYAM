# How to run NIYAM (for jurors)

Windows 10 or 11, with Python 3.11 or 3.12 (not 3.13 or newer: the backend refuses them), Node.js 20 or newer and git installed. No API key and no internet access are
needed after installation. In PowerShell:

```powershell
git clone <repository-url> NIYAM; cd NIYAM
cd backend; py -3.11 -m venv .venv; .venv\Scripts\Activate.ps1; pip install -e ".[dev]"; cd ..
cd frontend; npm ci; cd ..
.\scripts\demo.ps1        # starts the API and the web app and opens http://localhost:5173
# in the browser: "Open the app", then "Open sample A". Ctrl+C in PowerShell stops both servers.
```

If PowerShell refuses to run the scripts, allow local scripts for this window first:
`Set-ExecutionPolicy -Scope Process Bypass`.

On Linux or macOS use `./scripts/demo.sh` and `source .venv/bin/activate` instead.

**Without installing anything:** open https://nikhilmamilla.github.io/NIYAM/ (the dashboard is at `/NIYAM/app`).
It runs in demo mode: the 5 sample buildings show the results the real NIYAM engine produced, with the 3D view,
the clause cards and the HTML, JSON and BCF downloads; uploading your own IFC file needs the local install above.
The committed outputs for samples A to E are also in `submission/samples/`, and the screenshots in
`submission/screens/`.

**Without the web app:** `cd backend; .venv\Scripts\Activate.ps1; python -m app.audit.cli run ..\fixtures\samples\sample_a_mm.ifc --out ..\eval\runs\audit-demo`
prints the per-rule table and writes `report.json`, `report.html` and `issues.bcf`.
