from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator

from app.database import get_connection
from app.documents import create_document, get_document, list_documents
from app.processing import process_document
from app.search import search_chunks


app = FastAPI(title="RAG Docs Assistant")

MAX_UPLOAD_SIZE = 1_048_576

class DocumentCreate(BaseModel):
    filename: str
    content: str

    @field_validator("filename", "content")
    @classmethod
    def values_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field must not be blank")

        return value


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/health/db")
def database_health_check():
    with get_connection() as conn:
        conn.execute("SELECT 1")

    return {"status": "ok", "database": "connected"}

@app.post("/documents", status_code=201)
def create_document_endpoint(document: DocumentCreate):
    return create_document(
        filename=document.filename,
        content=document.content,
    )

@app.get("/documents/{document_id}")
def get_document_endpoint(document_id: int):
    document = get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document

@app.get("/documents")
def list_documents_endpoint():
    return list_documents()

@app.get("/search")
def search_endpoint(
    q: str,
    limit: int = 5,
    max_distance: float | None = None,
):
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be blank",
        )

    if limit < 1 or limit > 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20",
        )

    if max_distance is not None and max_distance < 0:
        raise HTTPException(
            status_code=400,
            detail="max_distance must be greater than or equal to 0",
        )

    results = search_chunks(
        query=q,
        limit=limit,
        max_distance=max_distance,
    )

    return {
        "query": q,
        "results": results,
    }


@app.post("/documents/upload", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are allowed",
        )

    content = bytearray()

    while True:
        chunk = await file.read(64 * 1024)

        if not chunk:
            break

        content.extend(chunk)

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds the maximum allowed size of 1 MiB",
            )

    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be encoded in UTF-8",
        )

    if not text_content.strip():
        raise HTTPException(
            status_code=400,
            detail="File cannot be empty",
        )

    document = create_document(
        filename=file.filename,
        content=text_content,
    )

    process_document(
        document_id=document["id"],
        content=document["content"],
    )

    return document
