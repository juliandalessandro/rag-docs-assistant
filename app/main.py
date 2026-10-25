from fastapi import FastAPI

app = FastAPI(title="RAG Docs Assistant")


@app.get("/health")
def health_check():
    return {"status": "ok"}