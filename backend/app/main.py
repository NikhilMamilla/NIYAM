from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit import router as audit_router
from app.config import Settings, settings


def create_app(s: Settings) -> FastAPI:
    """The web API has never exposed the LLM compiler, spec generation or evaluation (those are CLI only). A
    public deployment (DEPLOY_MODE=audit-only) also drops the interactive docs and schema, so it serves exactly
    /health, /api/samples, /api/rulepack, /api/audit and an audit's report and BCF downloads."""
    public = s.deploy_mode == "audit-only"
    app = FastAPI(title="NIYAM", docs_url=None if public else "/docs", redoc_url=None if public else "/redoc",
                  openapi_url=None if public else "/openapi.json")
    origins = s.cors_origins + [o.strip() for o in s.allowed_origins.split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])
    app.include_router(audit_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app(settings)
