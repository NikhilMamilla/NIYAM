import json
import uuid
import zipfile
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.fixtures.samples import SAMPLES_DIR
from app.main import app


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "audits"


@pytest.fixture
def client(data_dir):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, audit_data_dir=data_dir)
    yield TestClient(app)
    app.dependency_overrides.clear()


def upload(client, path=SAMPLES_DIR / "sample_a_mm.ifc", filename=None, content=None):
    data = content if content is not None else path.read_bytes()
    return client.post("/api/audit", files={"file": (filename or path.name, data, "application/octet-stream")})


def test_audit_happy_path_and_downloads(client, data_dir):
    truth = json.loads((SAMPLES_DIR / "sample_a_mm.truth.json").read_text(encoding="utf-8"))
    r = upload(client)
    assert r.status_code == 200, r.text
    body = r.json()
    audit_id = str(uuid.UUID(body["audit_id"]))
    assert body["status"] == truth["expected_status"]
    assert body["summary"] == {"passed": 17, "failed": 6, "unchecked": 7, "out_of_scope": 6}
    assert [rule["unit_id"] for rule in body["rules"]] == ["MBBL2016-5.4.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.1#c"]
    assert (data_dir / audit_id / "model.ifc").read_bytes() == (SAMPLES_DIR / "sample_a_mm.ifc").read_bytes()

    got = client.get(f"/api/audit/{audit_id}")
    assert got.status_code == 200 and got.json()["audit_id"] == audit_id and got.json()["status"] == body["status"]

    html = client.get(f"/api/audit/{audit_id}/report.html")
    assert html.status_code == 200 and html.headers["content-type"].startswith("text/html")
    assert "attachment" not in html.headers["content-disposition"] and audit_id in html.headers["content-disposition"]
    assert "NIYAM audit report" in html.text

    bcf = client.get(f"/api/audit/{audit_id}/issues.bcf")
    assert bcf.status_code == 200 and bcf.headers["content-type"] == "application/octet-stream"
    assert bcf.headers["content-disposition"].startswith("attachment")
    assert "bcf.version" in zipfile.ZipFile(BytesIO(bcf.content)).namelist()


def test_metre_sample_audits_too(client):
    r = upload(client, SAMPLES_DIR / "sample_b_m.ifc")
    assert r.status_code == 200 and r.json()["summary"]["failed"] == 4


def test_client_filename_is_never_used_for_paths(client, data_dir):
    r = upload(client, filename="../../evil name.ifc")
    assert r.status_code == 200
    [audit_dir] = list(data_dir.iterdir())
    assert sorted(p.name for p in audit_dir.iterdir()) == ["issues.bcf", "model.ifc", "report.html", "report.json"]
    assert not (data_dir.parent / "evil name.ifc").exists()


def test_oversize_upload_rejected(data_dir):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, audit_data_dir=data_dir,
                                                              max_upload_mb=0.001)
    try:
        r = upload(TestClient(app))
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 413 and "MB" in r.json()["detail"]
    assert not data_dir.exists() or not any(data_dir.iterdir())


def test_non_ifc_extension_rejected(client, data_dir):
    r = upload(client, filename="model.txt")
    assert r.status_code == 415 and ".ifc" in r.json()["detail"]
    assert not data_dir.exists() or not any(data_dir.iterdir())


def test_garbage_with_ifc_extension_is_422(client, data_dir):
    r = upload(client, filename="garbage.ifc", content=b"this is not a STEP file")
    assert r.status_code == 422 and "could not read IFC" in r.json()["detail"]
    assert not any(data_dir.iterdir())


@pytest.mark.parametrize("bad_id", ["..%2F..%2Fsecrets", "not-a-uuid", "..", "%2E%2E", "1234"])
@pytest.mark.parametrize("suffix", ["", "/report.html", "/issues.bcf"])
def test_non_uuid_ids_are_rejected_without_filesystem_access(client, bad_id, suffix):
    r = client.get(f"/api/audit/{bad_id}{suffix}")
    assert r.status_code in (404, 422)


def test_unknown_uuid_is_404(client):
    assert client.get(f"/api/audit/{uuid.uuid4()}").status_code == 404
    assert client.get(f"/api/audit/{uuid.uuid4()}/report.html").status_code == 404


def test_rulepack_endpoint(client):
    r = client.get("/api/rulepack")
    assert r.status_code == 200
    rules = r.json()["rules"]
    assert [x["unit_id"] for x in rules] == ["MBBL2016-5.4.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.1#c"]
    assert all(x["human_reviewed"] is False and x["clause_text"] and x["rule_text"] for x in rules)


def test_cors_allows_configured_dev_origin(client):
    r = client.options("/api/rulepack", headers={"Origin": "http://localhost:5173",
                                                  "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    r = client.options("/api/rulepack", headers={"Origin": "http://evil.example",
                                                  "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers
