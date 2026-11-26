"""The static demo (frontend/public/demo/, served by GitHub Pages) must be exactly what the engine produces now.

Re-runs every sample through the same API endpoints the dashboard calls and compares with the committed files:
JSON and HTML byte for byte (audit_id aside, a fresh UUID per run), the BCF topic by topic (its GUIDs are
random per export), the IFC byte for byte. Regenerate with `python scripts/build_demo_data.py`."""

import json
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from app.config import Settings, get_settings
from app.fixtures.samples import SAMPLES_DIR
from app.main import app

DEMO = Path(__file__).resolve().parents[2] / "frontend" / "public" / "demo"
FIX = "regenerate with `python scripts/build_demo_data.py`"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("audits")
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, audit_data_dir=data_dir)
    yield TestClient(app)
    app.dependency_overrides.clear()


def saved(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("audit_id", None)
    return data


def bcf_topics(content: bytes) -> list[tuple]:
    """Everything a BCF consumer sees, minus the per-export random GUIDs of topics and viewpoints."""
    z = zipfile.ZipFile(BytesIO(content))
    topics = []
    for name in z.namelist():
        if not name.endswith("/markup.bcf"):
            continue
        folder = name.split("/")[0]
        markup = etree.fromstring(z.read(name))
        t = markup.find("Topic")
        selected = []
        for vp in markup.iter("Viewpoints"):
            visinfo = etree.fromstring(z.read(f"{folder}/{vp.findtext('Viewpoint')}"))
            selected += [c.get("IfcGuid") for c in visinfo.iter("Component")]
        topics.append((t.findtext("Title"), t.findtext("Description"), t.findtext("Priority"),
                       tuple(l.text for l in t.iter("Labels")), tuple(sorted(selected))))
    return sorted(topics)


def test_sample_list_and_rulepack_match(client):
    assert DEMO.is_dir(), f"no demo data; {FIX}"
    assert json.loads((DEMO / "samples.json").read_text(encoding="utf-8")) == client.get("/api/samples").json(), FIX
    assert json.loads((DEMO / "rulepack.json").read_text(encoding="utf-8")) == client.get("/api/rulepack").json(), FIX


@pytest.mark.parametrize("name", sorted(p.stem for p in SAMPLES_DIR.glob("*.ifc")))
def test_demo_files_match_the_engine(client, name):
    d = DEMO / name
    r = client.post(f"/api/samples/{name}/audit")
    assert r.status_code == 200, r.text
    fresh = r.json()
    aid = fresh.pop("audit_id")
    assert saved(d / "audit.json") == fresh, f"{name}/audit.json drifted; {FIX}"
    report = client.get(f"/api/audit/{aid}").json()
    report.pop("audit_id")
    assert saved(d / "report.json") == report, f"{name}/report.json drifted; {FIX}"
    assert (d / "report.html").read_bytes() == client.get(f"/api/audit/{aid}/report.html").content, \
        f"{name}/report.html drifted; {FIX}"
    fresh_bcf = bcf_topics(client.get(f"/api/audit/{aid}/issues.bcf").content)
    assert fresh_bcf, "a sample with no BCF topics would not exercise the download"
    assert bcf_topics((d / "issues.bcf").read_bytes()) == fresh_bcf, f"{name}/issues.bcf drifted; {FIX}"
    assert (d / f"{name}.ifc").read_bytes() == (SAMPLES_DIR / f"{name}.ifc").read_bytes(), FIX
