"""DEPLOY_MODE=audit-only, the public deployment (render.yaml): only the audit surface, nothing kept on disk,
20 MB and IFC-only uploads, a per-IP rate limit."""

import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import audit as audit_api
from app.config import Settings, get_settings
from app.fixtures.samples import SAMPLES_DIR
from app.main import create_app

SAMPLE_A = SAMPLES_DIR / "sample_a_mm.ifc"


@pytest.fixture
def public(tmp_path):
    s = Settings(_env_file=None, deploy_mode="audit-only", audit_data_dir=tmp_path / "audits", rate_limit_per_minute=3,
                 allowed_origins="https://nikhilmamilla.github.io")
    app = create_app(s)
    app.dependency_overrides[get_settings] = lambda: s
    audit_api.rate_limit.hits.clear()
    audit_api.memory_exports.items.clear()
    yield TestClient(app), s
    audit_api.rate_limit.hits.clear()


def temp_dirs() -> set[str]:
    return {p.name for p in Path(tempfile.gettempdir()).glob("niyam-*")}


def upload(client, data: bytes, name="model.ifc"):
    return client.post("/api/audit", files={"file": (name, data, "application/octet-stream")})


def test_only_the_audit_surface_is_exposed(public):
    client, _ = public
    paths = set(client.app.openapi()["paths"])  # generated in-process; the public app does not serve it
    assert paths == {"/health", "/api/audit", "/api/samples", "/api/samples/{name}", "/api/samples/{name}/audit",
                     "/api/audit/{audit_id}", "/api/audit/{audit_id}/report.html", "/api/audit/{audit_id}/issues.bcf",
                     "/api/rulepack"}
    for gone in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(gone).status_code == 404
    r = client.get("/health", headers={"origin": "https://nikhilmamilla.github.io"})
    assert r.headers["access-control-allow-origin"] == "https://nikhilmamilla.github.io"


def test_audit_and_downloads_leave_nothing_on_disk(public):
    client, s = public
    before = temp_dirs()
    r = upload(client, SAMPLE_A.read_bytes(), "sample_a_mm.ifc")
    assert r.status_code == 200, r.text
    aid = r.json()["audit_id"]
    assert client.get(f"/api/audit/{aid}").json()["summary"] == r.json()["summary"]
    assert "NIYAM audit report" in client.get(f"/api/audit/{aid}/report.html").text
    bcf = client.get(f"/api/audit/{aid}/issues.bcf")
    assert bcf.headers["content-disposition"].startswith("attachment")
    assert "bcf.version" in zipfile.ZipFile(BytesIO(bcf.content)).namelist()
    assert client.post("/api/samples/sample_b_m/audit").status_code == 200
    assert not s.audit_data_dir.exists(), "audit-only must not write the audit folder"
    assert temp_dirs() == before, "the temp folder must be deleted after the audit"


def test_rejects_non_ifc_content_and_oversized_files(public):
    client, _ = public
    r = upload(client, b"PK\x03\x04 this is a zip, not an IFC")
    assert r.status_code == 415 and "not an IFC file" in r.json()["detail"]
    assert upload(client, b"ISO-10303-21;", "model.txt").status_code == 415
    big = b"ISO-10303-21;\n" + b"x" * (21 * 1024 * 1024)
    r = upload(client, big)
    assert r.status_code == 413 and "20 MB" in r.json()["detail"]


def test_rate_limit_per_client_ip(public):
    client, _ = public
    codes = [client.post("/api/samples/sample_c_no_fireexit_mm/audit", headers={"x-forwarded-for": "203.0.113.9"})
             .status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    # another address is counted separately; a spoofed first X-Forwarded-For entry does not dodge the limit
    assert client.post("/api/samples/sample_c_no_fireexit_mm/audit",
                       headers={"x-forwarded-for": "198.51.100.7"}).status_code == 200
    assert client.post("/api/samples/sample_c_no_fireexit_mm/audit",
                       headers={"x-forwarded-for": "1.2.3.4, 203.0.113.9"}).status_code == 429


def test_full_mode_is_unchanged_by_default():
    assert Settings(_env_file=None).deploy_mode == "full"
