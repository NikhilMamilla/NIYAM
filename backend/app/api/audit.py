"""Audit upload API. Uploaded files are stored under <audit_data_dir>/<uuid4>/model.ifc; the client's
filename is only used to check the extension, never to build a path.

DEPLOY_MODE=audit-only (the public deployment) changes four things: the model goes to a temp folder that is
deleted right after the audit, the three exports are kept in a small in-memory store instead of on disk, uploads
are capped at 20 MB and must start like an IFC (STEP) file, and audits are rate-limited per client IP."""

import json
import logging
import shutil
import tempfile
import threading
import time
import uuid
from collections import OrderedDict, defaultdict, deque
from collections.abc import Awaitable, Callable
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from starlette.concurrency import run_in_threadpool

from app.audit.cli import write_outputs
from app.audit.engine import InvalidIfcError, audit
from app.config import Settings, get_settings
from app.fixtures.samples import DESCRIPTIONS, SAMPLES_DIR
from app.rulepack.loader import Rulepack, load_rulepack

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
CHUNK = 1024 * 1024
PUBLIC_MAX_MB = 20.0
EXPORTS = ("report.json", "report.html", "issues.bcf")


@lru_cache
def get_rulepack() -> Rulepack:
    return load_rulepack()


def _public(settings: Settings) -> bool:
    return settings.deploy_mode == "audit-only"


class _MemoryExports:
    """audit-only: the last audits' exports, in memory, oldest dropped first. Nothing is written to disk."""

    def __init__(self, keep: int = 64):
        self.keep, self.items, self.lock = keep, OrderedDict(), threading.Lock()

    def put(self, audit_id: str, files: dict[str, bytes]) -> None:
        with self.lock:
            self.items[audit_id] = files
            while len(self.items) > self.keep:
                self.items.popitem(last=False)

    def get(self, audit_id: str, name: str) -> bytes:
        with self.lock:
            files = self.items.get(audit_id)
        if files is None:
            raise HTTPException(404, "audit not found")
        return files[name]


class _RateLimit:
    """audit-only: at most `per_minute` audits per client IP in any 60 s window."""

    def __init__(self):
        self.hits, self.lock = defaultdict(deque), threading.Lock()

    def check(self, client: str, per_minute: int) -> None:
        now = time.monotonic()
        with self.lock:
            hits = self.hits[client]
            while hits and now - hits[0] > 60:
                hits.popleft()
            if len(hits) >= per_minute:
                raise HTTPException(429, "too many audits from this address; try again in a minute")
            hits.append(now)


memory_exports = _MemoryExports()
rate_limit = _RateLimit()


def limit_rate(request: Request, settings: Settings = Depends(get_settings)) -> None:
    if not _public(settings):
        return
    # Render's proxy appends the address it saw to X-Forwarded-For: the last entry cannot be set by the client
    forwarded = request.headers.get("x-forwarded-for", "")
    client = forwarded.split(",")[-1].strip() or (request.client.host if request.client else "unknown")
    rate_limit.check(client, settings.rate_limit_per_minute)


def _audit_dir(settings: Settings, audit_id: uuid.UUID) -> Path:
    # audit_id is a parsed UUID, so str() is the canonical 36-character form: no path separators
    path = settings.audit_data_dir / str(audit_id)
    if not path.is_dir():
        raise HTTPException(404, "audit not found")
    return path


def _export(settings: Settings, audit_id: uuid.UUID, name: str, media_type: str, filename: str,
            inline: bool = False):
    if _public(settings):
        disposition = "inline" if inline else "attachment"
        return Response(memory_exports.get(str(audit_id), name), media_type=media_type,
                        headers={"content-disposition": f'{disposition}; filename="{filename}"'})
    return FileResponse(_audit_dir(settings, audit_id) / name, media_type=media_type, filename=filename,
                        content_disposition_type="inline" if inline else "attachment")


async def _run_audit(settings: Settings, store: Callable[[Path], Awaitable[None]], shown_name: str) -> dict:
    """Create a fresh audit folder, let `store` write model.ifc into it, audit it, write the exports.
    The reports name the model `shown_name` (display only, never a path). Any failure removes the folder.
    In audit-only mode the folder is a temp folder, removed in every case once the exports are in memory."""
    audit_id = uuid.uuid4()
    public = _public(settings)
    if public:
        audit_dir = Path(tempfile.mkdtemp(prefix="niyam-"))
    else:
        audit_dir = settings.audit_data_dir / str(audit_id)
        audit_dir.mkdir(parents=True)
    model_path = audit_dir / "model.ifc"
    try:
        await store(model_path)
        try:
            report = await run_in_threadpool(  # CPU bound
                audit, model_path, get_rulepack(), geometric_timeout_s=settings.geometric_timeout_s)
            report = report.model_copy(update={"ifc_file": shown_name})
            await run_in_threadpool(write_outputs, report, audit_dir)
        except InvalidIfcError as e:
            raise HTTPException(422, str(e)) from e
        except Exception as e:
            log.exception("audit %s failed", audit_id)  # traceback stays server-side
            raise HTTPException(500, "internal error while auditing the model") from e
        if public:
            memory_exports.put(str(audit_id), {n: (audit_dir / n).read_bytes() for n in EXPORTS})
    except BaseException:
        shutil.rmtree(audit_dir, ignore_errors=True)
        raise
    finally:
        if public:
            shutil.rmtree(audit_dir, ignore_errors=True)
    return {"audit_id": str(audit_id), "status": report.status, "summary": report.summary.model_dump(),
            "rules": [r.model_dump() for r in report.rules]}


@router.post("/audit", dependencies=[Depends(limit_rate)])
async def create_audit(file: UploadFile, request: Request, settings: Settings = Depends(get_settings)):
    if not (file.filename or "").lower().endswith(".ifc"):
        raise HTTPException(415, "only .ifc files are accepted")
    public = _public(settings)
    max_mb = min(settings.max_upload_mb, PUBLIC_MAX_MB) if public else settings.max_upload_mb
    limit = int(max_mb * 1024 * 1024)
    too_big = HTTPException(413, f"file exceeds the {max_mb:g} MB upload limit")
    if public and int(request.headers.get("content-length") or 0) > limit + CHUNK:  # form overhead allowance
        raise too_big

    async def store(model_path: Path) -> None:
        size = 0
        with open(model_path, "wb") as out:
            while chunk := await file.read(CHUNK):
                if public and size == 0 and not chunk.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"ISO-10303-21"):
                    raise HTTPException(415, "this is not an IFC file (an IFC file starts with ISO-10303-21)")
                size += len(chunk)
                if size > limit:
                    raise too_big
                out.write(chunk)

    return await _run_audit(settings, store, Path((file.filename or "model.ifc").replace("\\", "/")).name)


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


@router.post("/samples/{name}/audit", dependencies=[Depends(limit_rate)])
async def audit_sample(name: str, settings: Settings = Depends(get_settings)):
    source = _sample(name)

    async def store(model_path: Path) -> None:
        shutil.copyfile(source, model_path)

    return await _run_audit(settings, store, source.name)


@router.get("/audit/{audit_id}")
def get_audit(audit_id: uuid.UUID, settings: Settings = Depends(get_settings)):
    if _public(settings):
        data = json.loads(memory_exports.get(str(audit_id), "report.json"))
    else:
        data = json.loads((_audit_dir(settings, audit_id) / "report.json").read_text(encoding="utf-8"))
    return {"audit_id": str(audit_id), **data}


@router.get("/audit/{audit_id}/report.html")
def get_report_html(audit_id: uuid.UUID, settings: Settings = Depends(get_settings)):
    return _export(settings, audit_id, "report.html", "text/html; charset=utf-8", f"niyam-audit-{audit_id}.html",
                   inline=True)


@router.get("/audit/{audit_id}/issues.bcf")
def get_issues_bcf(audit_id: uuid.UUID, settings: Settings = Depends(get_settings)):
    return _export(settings, audit_id, "issues.bcf", "application/octet-stream", f"niyam-issues-{audit_id}.bcf")


@router.get("/rulepack")
def get_rulepack_rules():
    pack = get_rulepack()
    return {"version": pack.manifest.version, "rules": [
        {"unit_id": r.unit_id, "clause_id": r.clause_id, "clause_text": r.clause_text, "rule_text": r.rule_text,
         "source_doc": r.source_doc, "page": r.page, "severity": r.severity, "human_reviewed": r.human_reviewed}
        for r in pack.manifest.rules]}
