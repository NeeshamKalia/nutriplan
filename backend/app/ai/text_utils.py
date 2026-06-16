"""Text utilities for RAG chunking."""

import re

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    cleaned = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split plain text into overlapping chunks for embedding."""
    text = strip_html(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
            continue

        if current:
            chunks.append(current)

        if len(para) <= chunk_size:
            current = para
            continue

        step = max(chunk_size - overlap, 1)
        for start in range(0, len(para), step):
            chunks.append(para[start : start + chunk_size])
        current = ""

    if current:
        chunks.append(current)

    return chunks
