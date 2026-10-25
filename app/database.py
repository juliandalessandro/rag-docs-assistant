import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection(db_name: str | None = None):
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "rag_docs"),
        user=os.getenv("DB_USER", "rag_user"),
        password=os.getenv("DB_PASSWORD", ""),
    )