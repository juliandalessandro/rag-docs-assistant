from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator

from app.database import get_connection
from app.documents import create_document, get_document, list_documents


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

    return create_document(
        filename=file.filename,
        content=text_content,
    )