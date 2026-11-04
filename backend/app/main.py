from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit import router as audit_router
from app.config import settings

app = FastAPI(title="NIYAM")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"],
                   allow_headers=["*"])
app.include_router(audit_router)


@app.get("/health")
def health():
    return {"status": "ok"}
