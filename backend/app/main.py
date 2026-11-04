from fastapi import FastAPI

app = FastAPI(title="NIYAM")


@app.get("/health")
def health():
    return {"status": "ok"}
