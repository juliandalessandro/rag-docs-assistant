
from app.chunks import create_chunks
from app.documents import create_document
from app.database import get_connection
from app.processing import process_document


def test_create_chunks_saves_chunks_in_database():
    document = create_document(
        filename="test.txt",
        content="Original document content.",
    )

    chunks = ["First segment", "Second segment"]

    created_chunks = create_chunks(
        document_id=document["id"],
        chunks=chunks,
    )


    assert len(created_chunks) == 2

    assert created_chunks[0]["document_id"] == document["id"]
    assert created_chunks[0]["chunk_index"] == 0
    assert created_chunks[0]["content"] == "First segment"

    assert created_chunks[1]["document_id"] == document["id"]
    assert created_chunks[1]["chunk_index"] == 1
    assert created_chunks[1]["content"] == "Second segment"

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT chunk_index, content
            FROM document_chunks
            WHERE document_id = %s
            ORDER BY chunk_index
            """,
            (document["id"],),
        ).fetchall()

    assert rows == [
        (0, "First segment"),
        (1, "Second segment"),
    ]

def test_create_chunks_with_empty_list_returns_empty_list():
    created_chunks = create_chunks(
        document_id=1,
        chunks=[],
    )

    assert created_chunks == []

def test_create_chunks_with_single_chunk():
    document = create_document(
        filename="single_chunk.txt",
        content="This document contains a single chunk.",
    )

    created_chunks = create_chunks(
        document_id=document["id"],
        chunks=["Only one chunk"],
    )

    assert len(created_chunks) == 1
    assert created_chunks[0]["document_id"] == document["id"]
    assert created_chunks[0]["chunk_index"] == 0
    assert created_chunks[0]["content"] == "Only one chunk"

def test_process_document_splits_and_saves_chunks():
    document = create_document(
        filename="processing_test.txt",
        content="ABCDEFGHIJ",
    )

    created_chunks = process_document(
        document_id=document["id"],
        content=document["content"],
        chunk_size=4,
        overlap=1,
    )

    assert len(created_chunks) == 3

    assert created_chunks[0]["chunk_index"] == 0
    assert created_chunks[0]["content"] == "ABCD"

    assert created_chunks[1]["chunk_index"] == 1
    assert created_chunks[1]["content"] == "DEFG"

    assert created_chunks[2]["chunk_index"] == 2
    assert created_chunks[2]["content"] == "GHIJ"