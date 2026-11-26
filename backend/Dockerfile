# NIYAM API for a public deployment (render.yaml), DEPLOY_MODE=audit-only. Build from the repository root,
# because the API reads the rulepack and the sample buildings:
#   docker build -f backend/Dockerfile -t niyam-api .
#   docker run --rm -p 8000:8000 niyam-api
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEPLOY_MODE=audit-only MAX_UPLOAD_MB=20 PORT=8000

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/app backend/app
COPY rules/rulepack rules/rulepack
COPY fixtures/samples fixtures/samples

RUN useradd --create-home --uid 10001 niyam
USER niyam
WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=4)"
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
