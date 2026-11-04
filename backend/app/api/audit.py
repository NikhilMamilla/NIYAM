"""Audit upload API. Uploaded files are stored under <audit_data_dir>/<uuid4>/model.ifc; the client's
filename is only used to check the extension, never to build a path."""

import json
import logging
import shutil
import uuid
from collections.abc import Awaitable, Callable
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.audit.cli import write_outputs
from app.audit.engine import InvalidIfcError, audit
from app.config import Settings, get_settings
from app.fixtures.samples import DESCRIPTIONS, SAMPLES_DIR
from app.rulepack.loader import Rulepack, load_rulepack

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
CHUNK = 1024 * 1024


@lru_cache
def get_rulepack() -> Rulepack:
    return load_rulepack()


def _audit_dir(settings: Settings, audit_id: uuid.UUID) -> Path:
    # audit_id is a parsed UUID, so str() is the canonical 36-character form: no path separators
    path = settings.audit_data_dir / str(audit_id)
    if not path.is_dir():
        raise HTTPException(404, "audit not found")
    return path


async def _run_audit(settings: Settings, store: Callable[[Path], Awaitable[None]]) -> dict:
    """Create a fresh audit folder, let `store` write model.ifc into it, audit it, write the exports.
    Any failure removes the folder."""
    audit_id = uuid.uuid4()
    audit_dir = settings.audit_data_dir / str(audit_id)
    audit_dir.mkdir(parents=True)
    model_path = audit_dir / "model.ifc"
    try:
        await store(model_path)
        try:
            report = await run_in_threadpool(  # CPU bound
                audit, model_path, get_rulepack(), geometric_timeout_s=settings.geometric_timeout_s)
            await run_in_threadpool(write_outputs, report, audit_dir)
        except InvalidIfcError as e:
            raise HTTPException(422, str(e)) from e
        except Exception as e:
            log.exception("audit %s failed", audit_id)  # traceback stays server-side
            raise HTTPException(500, "internal error while auditing the model") from e
    except BaseException:
        shutil.rmtree(audit_dir, ignore_errors=True)
        raise
    return {"audit_id": str(audit_id), "status": report.status, "summary": report.summary.model_dump(),
            "rules": [r.model_dump() for r in report.rules]}


@router.post("/audit")
async def create_audit(file: UploadFile, settings: Settings = Depends(get_settings)):
    if not (file.filename or "").lower().endswith(".ifc"):
        raise HTTPException(415, "only .ifc files are accepted")
    limit = int(settings.max_upload_mb * 1024 * 1024)

    async def store(model_path: Path) -> None:
        size = 0
        with open(model_path, "wb") as out:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"file exceeds the {settings.max_upload_mb:g} MB upload limit")
                out.write(chunk)

    return await _run_audit(settings, store)


def _samples() -> dict[str, Path]:
    """The allowlist: exactly the committed sample files, keyed by name. User input only ever looks up a key."""
    return {p.stem: p for p in sorted(SAMPLES_DIR.glob("*.ifc"))}


def _sample(name: str) -> Path:
    path = _samples().get(name)
    if path is None:
        raise HTTPException(404, "sample not found")
    return path


@router.get("/samples")
def list_samples():
    return [{"name": name, "description": DESCRIPTIONS.get(name, "Synthetic sample model."),
             "size_bytes": path.stat().st_size} for name, path in _samples().items()]


@router.get("/samples/{name}")
def get_sample(name: str):
    path = _sample(name)
    return FileResponse(path, media_type="application/octet-stream", filename=path.name)


@router.post("/samples/{name}/audit")
async def audit_sample(name: str, settings: Settings = Depends(get_settings)):
    source = _sample(name)

    async def store(model_path: Path) -> None:
        shutil.copyfile(source, model_path)

    return await _run_audit(settings, store)


@router.get("/audit/{audit_id}")
def get_audit(audit_id: uuid.UUID, settings: Settings = Depends(get_settings)):
    data = json.loads((_audit_dir(settings, audit_id) / "report.json").read_text(encoding="utf-8"))
    return {"audit_id": str(audit_id), **data}


@router.get("/audit/{audit_id}/report.html")
def get_report_html(audit_id: uuid.UUID, settings: Settings = Depends(get_settings)):
    return FileResponse(_audit_dir(settings, audit_id) / "report.html", media_type="text/html; charset=utf-8",
                        filename=f"niyam-audit-{audit_id}.html", content_disposition_type="inline")


@router.get("/audit/{audit_id}/issues.bcf")
def get_issues_bcf(audit_id: uuid.UUID, settings: Settings = Depends(get_settings)):
    return FileResponse(_audit_dir(settings, audit_id) / "issues.bcf", media_type="application/octet-stream",
                        filename=f"niyam-issues-{audit_id}.bcf")


@router.get("/rulepack")
def get_rulepack_rules():
    pack = get_rulepack()
    return {"version": pack.manifest.version, "rules": [
        {"unit_id": r.unit_id, "clause_id": r.clause_id, "clause_text": r.clause_text, "rule_text": r.rule_text,
         "source_doc": r.source_doc, "page": r.page, "severity": r.severity, "human_reviewed": r.human_reviewed}
        for r in pack.manifest.rules]}
