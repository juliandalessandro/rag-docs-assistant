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

def test_upload_text_file_creates_chunks():
    files = {
        "file": (
            "chunked_upload.txt",
            "This is the content that should be stored as a chunk.",
            "text/plain",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 201

    document_id = response.json()["id"]

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                document_id,
                chunk_index,
                content,
                vector_dims(embedding),
                embedding IS NOT NULL
            FROM document_chunks
            WHERE document_id = %s
            ORDER BY chunk_index
            """,
            (document_id,),
        ).fetchall()

    assert len(rows) == 1
    assert rows[0][:3] == (
        document_id,
        0,
        "This is the content that should be stored as a chunk.",
    )
    assert rows[0][3] == 384
    assert rows[0][4] is True

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

def test_search_endpoint_returns_results():
    with get_connection() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (filename, content)
            VALUES (%s, %s)
            RETURNING id
            """,
            ("api_search_test.txt", "Content for API search testing."),
        ).fetchone()

        document_id = document[0]

        conn.execute(
            """
            INSERT INTO document_chunks (
                document_id,
                chunk_index,
                content,
                embedding
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                document_id,
                0,
                "The capital of France is Paris.",
                [1.0] + [0.0] * 383,
            ),
        )

    response = client.get("/search?q=capital%20of%20France&limit=3")

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "capital of France"
    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "The capital of France is Paris."


def test_search_endpoint_rejects_blank_query():
    response = client.get("/search?q=%20%20%20")

    assert response.status_code == 400
    assert response.json()["detail"] == "Search query cannot be blank"


def test_search_endpoint_rejects_invalid_limit():
    response = client.get("/search?q=test&limit=0")

    assert response.status_code == 400
    assert response.json()["detail"] == "Limit must be between 1 and 20"

def test_search_endpoint_requires_query():
    response = client.get("/search")

    assert response.status_code == 422


def test_search_endpoint_rejects_non_integer_limit():
    response = client.get("/search?q=test&limit=abc")

    assert response.status_code == 422

def test_search_endpoint_rejects_negative_max_distance():
    response = client.get(
        "/search?q=test&max_distance=-0.5"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "max_distance must be greater than or equal to 0"
    )

def test_search_endpoint_passes_max_distance_to_search_chunks(monkeypatch):
    from app import main

    captured_params = {}

    def fake_search_chunks(query, limit, max_distance):
        captured_params["query"] = query
        captured_params["limit"] = limit
        captured_params["max_distance"] = max_distance
        return []

    monkeypatch.setattr(main, "search_chunks", fake_search_chunks)

    response = client.get(
        "/search?q=test&limit=3&max_distance=0.5"
    )

    assert response.status_code == 200
    assert captured_params == {
        "query": "test",
        "limit": 3,
        "max_distance": 0.5,
    }
    assert response.json() == {
        "query": "test",
        "results": [],
    }


def test_search_endpoint_filters_results_by_max_distance(monkeypatch):
    from app import search

    monkeypatch.setattr(
        "app.search.generate_embedding",
        lambda text: [1.0] + [0.0] * 383,
    )

    with get_connection() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (filename, content)
            VALUES (%s, %s)
            RETURNING id
            """,
            ("api_distance_test.txt", "Distance filter test"),
        ).fetchone()

        document_id = document[0]

        conn.execute(
            """
            INSERT INTO document_chunks (
                document_id,
                chunk_index,
                content,
                embedding
            )
            VALUES
                (%s, %s, %s, %s),
                (%s, %s, %s, %s),
                (%s, %s, %s, %s)
            """,
            (
                document_id, 0, "Same direction",
                [1.0] + [0.0] * 383,
                document_id, 1, "Perpendicular direction",
                [0.0, 1.0] + [0.0] * 382,
                document_id, 2, "Opposite direction",
                [-1.0] + [0.0] * 383,
            ),
        )

    response = client.get(
        "/search?q=test&max_distance=1.0"
    )

    assert response.status_code == 200

    results = response.json()["results"]

    assert [result["content"] for result in results] == [
        "Same direction",
        "Perpendicular direction",
    ]
