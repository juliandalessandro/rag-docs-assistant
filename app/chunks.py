from app.database import get_connection
from app.embeddings import generate_embedding


def create_chunks(document_id: int, chunks: list[str]) -> list[dict]:
    created_chunks = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            for chunk_index, content in enumerate(chunks):
                embedding = generate_embedding(content)

                cur.execute(
                    """
                    INSERT INTO document_chunks (
                        document_id,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, document_id, chunk_index, content, created_at
                    """,
                    (document_id, chunk_index, content, embedding),
                )

                row = cur.fetchone()

                created_chunks.append({
                    "id": row[0],
                    "document_id": row[1],
                    "chunk_index": row[2],
                    "content": row[3],
                    "created_at": row[4],
                })

    return created_chunks