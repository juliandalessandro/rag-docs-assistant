from app.database import get_connection


def create_document(filename: str, content: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO documents (filename, content)
            VALUES (%s, %s)
            RETURNING id, filename, content, created_at
            """,
            (filename, content)
        ).fetchone()

    return {
        "id": row[0],
        "filename": row[1],
        "content": row[2],
        "created_at": row[3]
    }

def get_document(document_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, filename, content, created_at
            FROM documents
            WHERE id = %s
            """,
            (document_id,)
        ).fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "filename": row[1],
            "content": row[2],
            "created_at": row[3]
        }