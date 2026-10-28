
from app.chunking import split_text
from app.chunks import create_chunks


def process_document(
    document_id: int,
    content: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    chunks = split_text(
        text=content,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    return create_chunks(
        document_id=document_id,
        chunks=chunks,
    )