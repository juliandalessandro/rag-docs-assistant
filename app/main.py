from fastapi import FastAPI

from app.database import get_connection


app = FastAPI(title="RAG Docs Assistant")


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/health/db")
def database_health_check():
    with get_connection() as conn:
        conn.execute("SELECT 1")

    return {"status": "ok", "database": "connected"}