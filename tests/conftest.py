import pytest

from app.database import get_connection


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    monkeypatch.setenv("DB_NAME", "rag_docs_test")


@pytest.fixture(autouse=True)
def clean_test_documents(use_test_database):
    with get_connection() as conn:
        database_name = conn.execute(
            "SELECT current_database()"
        ).fetchone()[0]

        if database_name != "rag_docs_test":
            raise RuntimeError(
                f"Refusing to clean database: {database_name}"
            )

        conn.execute("DELETE FROM documents")

    yield

    with get_connection() as conn:
        database_name = conn.execute(
            "SELECT current_database()"
        ).fetchone()[0]

        if database_name != "rag_docs_test":
            raise RuntimeError(
                f"Refusing to clean database: {database_name}"
            )

        conn.execute("DELETE FROM documents")
