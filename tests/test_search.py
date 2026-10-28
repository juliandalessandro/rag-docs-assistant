
from app.database import get_connection
from app.search import search_chunks


def test_search_chunks_returns_results():
    with get_connection() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (filename, content)
            VALUES (%s, %s)
            RETURNING id
            """,
            ("search_test.txt", "Content for search testing."),
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

    results = search_chunks(
        "capital of France",
        db_name="rag_docs_test",
    )

    assert len(results) == 1
    assert results[0]["content"] == "The capital of France is Paris."
    assert results[0]["document_id"] == document_id
    assert results[0]["distance"] >= 0


def test_search_chunks_returns_empty_list_when_no_chunks_exist():
    results = search_chunks(
        "some query",
        db_name="rag_docs_test",
    )

    assert results == []

def test_search_chunks_orders_results_by_cosine_distance():
    with get_connection() as conn:
        document = conn.execute(
            """
            INSERT INTO documents (filename, content)
            VALUES (%s, %s)
            RETURNING id
            """,
            ("search_order_test.txt", "Content for ordering tests."),
        ).fetchone()

        document_id = document[0]

        chunks = [
            (0, "Opposite direction", [-1.0] + [0.0] * 383),
            (1, "Perpendicular direction", [0.0, 1.0] + [0.0] * 382),
            (2, "Same direction", [1.0] + [0.0] * 383),
        ]

        for chunk_index, content, embedding in chunks:
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
                (document_id, chunk_index, content, embedding),
            )

    results = search_chunks(
        "test query",
        limit=3,
        db_name="rag_docs_test",
    )

    assert len(results) == 3
    assert [result["content"] for result in results] == [
        "Same direction",
        "Perpendicular direction",
        "Opposite direction",
    ]

def test_search_chunks_filters_results_by_max_distance(monkeypatch):
    from app.search import search_chunks

    monkeypatch.setattr(
        "app.search.generate_embedding",
        lambda text: [1.0] + [0.0] * 383,
    )

    with get_connection("rag_docs_test") as conn:
        document = conn.execute(
            """
            INSERT INTO documents (filename, content)
            VALUES (%s, %s)
            RETURNING id
            """,
            ("distance-test.txt", "Distance test document"),
        ).fetchone()

        document_id = document[0]

        conn.execute(
            """
            INSERT INTO document_chunks
                (document_id, chunk_index, content, embedding)
            VALUES
                (%s, 0, %s, %s),
                (%s, 1, %s, %s),
                (%s, 2, %s, %s)
            """,
            (
                document_id, "Same direction",
                [1.0] + [0.0] * 383,
                document_id, "Perpendicular direction",
                [0.0, 1.0] + [0.0] * 382,
                document_id, "Opposite direction",
                [-1.0] + [0.0] * 383,
            ),
        )

    results = search_chunks(
        query="test query",
        limit=5,
        db_name="rag_docs_test",
        max_distance=1.0,
    )

    assert [result["content"] for result in results] == [
        "Same direction",
        "Perpendicular direction",
    ]