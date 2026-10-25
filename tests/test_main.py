from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_database_connection():
    with get_connection() as conn:
        result = conn.execute(
            "SELECT current_database(), current_user"
        ).fetchone()
    
    assert result == ("rag_docs_test", "rag_user")

def test_database_health_check():
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}

def test_create_document():
    payload = {
        "filename": "test.txt",
        "content": "This is a test document."
    }

    response = client.post("/documents", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["filename"] == payload["filename"]
    assert data["content"] == payload["content"]
    assert "created_at" in data

def test_create_document_requires_filename_and_content():
    payload = {
        "filename": "",
        "content": ""
    }

    response = client.post("/documents", json=payload)

    assert response.status_code == 422

def test_create_document_rejects_whitespace():
    payload = {
        "filename": "   ",
        "content": "   ",
    }

    response = client.post("/documents", json=payload)

    assert response.status_code == 422

def test_get_document():
    create_payload = {
        "filename": "document_to_retrieve.txt",
        "content": "Content to verify document retrieval.",
    }

    create_response = client.post("/documents", json=create_payload)

    assert create_response.status_code == 201

    document_id = create_response.json()["id"]

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == document_id
    assert data["filename"] == create_payload["filename"]
    assert data["content"] == create_payload["content"]

def test_get_document_not_found():
    response = client.get("/documents/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}

def test_list_documents():
    create_payload = {
        "filename": "document_to_list.txt",
        "content": "Content to verify document listing.",
    }

    create_response = client.post("/documents", json=create_payload)

    assert create_response.status_code == 201

    response = client.get("/documents")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert any(
        document["id"] == create_response.json()["id"]
        for document in data
    )

def test_upload_text_file():
    files = {
        "file": (
            "upload_test.txt",
            "This is an uploaded test document.",
            "text/plain",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["filename"] == "upload_test.txt"
    assert data["content"] == "This is an uploaded test document."
    assert "created_at" in data

def test_upload_rejects_non_text_file():
    files = {
        "file": (
            "history.pdf",
            b"Fake PDF content",
            "application/pdf",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only .txt files are allowed"
    }

def test_upload_rejects_empty_file():
    files = {
        "file": (
            "empty.txt",
            "",
            "text/plain",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "File cannot be empty"
    }

def test_upload_rejects_invalid_utf8():
    files = {
        "file": (
            "invalid_encoding.txt",
            b"\xff\xfe\xfa",
            "text/plain",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "File must be encoded in UTF-8"
    }

def test_upload_rejects_file_over_size_limit():
    from app.main import MAX_UPLOAD_SIZE

    files = {
        "file": (
            "large.txt",
            b"A" * (MAX_UPLOAD_SIZE + 1),
            "text/plain",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 413
    assert response.json() == {
        "detail": "File exceeds the maximum allowed size of 1 MiB"
    }

def test_upload_accepts_file_at_size_limit():
    from app.main import MAX_UPLOAD_SIZE

    files = {
        "file": (
            "maximum_size.txt",
            b"A" * MAX_UPLOAD_SIZE,
            "text/plain",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "maximum_size.txt"
    assert len(data["content"].encode("utf-8")) == MAX_UPLOAD_SIZE