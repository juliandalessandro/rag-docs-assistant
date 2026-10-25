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
    
    assert result == ("rag_docs", "rag_user")
