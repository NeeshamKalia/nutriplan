"""Embedding generation for RAG using LangChain + Gemini."""

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_embeddings_client: GoogleGenerativeAIEmbeddings | None = None


def _get_embeddings_client() -> GoogleGenerativeAIEmbeddings:
    global _embeddings_client
    if _embeddings_client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for embeddings")
        _embeddings_client = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )
    return _embeddings_client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of text chunks."""
    if not texts:
        return []
    client = _get_embeddings_client()
    logger.info("Generating embeddings for %d chunks", len(texts))
    return await client.aembed_documents(texts)


async def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    client = _get_embeddings_client()
    return await client.aembed_query(text)
