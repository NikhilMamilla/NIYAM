"""Capture the real engine's results for the 5 sample buildings, for the static demo on GitHub Pages.

Calls exactly the endpoints the dashboard calls (GET /api/samples, GET /api/rulepack, POST
/api/samples/<name>/audit, GET /api/audit/<id>, .../report.html, .../issues.bcf) and saves the responses
unchanged under frontend/public/demo/, with each sample's IFC beside them. Nothing here is hand-written.
backend/tests/test_demo_data.py re-runs the audits and fails if these files drift from the engine.

Usage (repository root, backend venv):
  python scripts/build_demo_data.py                          # in-process, the same FastAPI app
  python scripts/build_demo_data.py --url http://127.0.0.1:8000   # against a running backend
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "demo"
sys.path.insert(0, str(ROOT / "backend"))


def client_for(url: str | None):
    import httpx
    if url:
        return httpx.Client(base_url=url, timeout=300)
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def get(c, path: str):
    r = c.get(path)
    r.raise_for_status()
    return r


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", help="base URL of a running backend; default: in-process")
    args = p.parse_args(argv)
    from app.fixtures.samples import SAMPLES_DIR

    c = client_for(args.url)
    OUT.mkdir(parents=True, exist_ok=True)
    samples = get(c, "/api/samples").json()
    (OUT / "samples.json").write_text(json.dumps(samples, indent=1), encoding="utf-8")
    (OUT / "rulepack.json").write_text(json.dumps(get(c, "/api/rulepack").json(), indent=1), encoding="utf-8")
    for s in samples:
        name = s["name"]
        d = OUT / name
        d.mkdir(exist_ok=True)
        r = c.post(f"/api/samples/{name}/audit")
        r.raise_for_status()
        audit = r.json()
        aid = audit["audit_id"]
        (d / "audit.json").write_text(json.dumps(audit, indent=1), encoding="utf-8")
        (d / "report.json").write_text(json.dumps(get(c, f"/api/audit/{aid}").json(), indent=1), encoding="utf-8")
        (d / "report.html").write_bytes(get(c, f"/api/audit/{aid}/report.html").content)
        (d / "issues.bcf").write_bytes(get(c, f"/api/audit/{aid}/issues.bcf").content)
        shutil.copyfile(SAMPLES_DIR / f"{name}.ifc", d / f"{name}.ifc")
        print(f"{name}: {audit['status']}, {audit['summary']['checks']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
