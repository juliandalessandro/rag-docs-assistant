
from pgvector import Vector

from app.database import get_connection
from app.embeddings import generate_embedding


def search_chunks(
    query: str,
    limit: int = 5,
    db_name: str | None = None,
    max_distance: float | None = None,
) -> list[dict]:
    query_embedding = Vector(generate_embedding(query))

    with get_connection(db_name) as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                embedding <=> %s AS distance
            FROM document_chunks
            WHERE embedding IS NOT NULL
            AND (%s::DOUBLE PRECISION IS NULL OR embedding <=> %s <= %s)
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (
                query_embedding,
                max_distance,
                query_embedding,
                max_distance,
                query_embedding,
                limit,
            ),
        ).fetchall()

    return [
        {
            "id": row[0],
            "document_id": row[1],
            "chunk_index": row[2],
            "content": row[3],
            "distance": row[4],
        }
        for row in rows
    ]