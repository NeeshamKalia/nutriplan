"""RAG-powered Q&A from dietitian articles."""

import uuid as uuid_mod

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_query
from app.config import settings
from app.core.logger import get_logger
from app.services.article_embedding_service import search_relevant_chunks

logger = get_logger(__name__)

RAG_SYSTEM_PROMPT = """You are a helpful nutrition assistant for Indian clients.
Answer the client's question using ONLY the article excerpts provided below.
If the excerpts don't contain enough information, say you couldn't find a clear answer
and suggest asking their dietitian directly.
Keep answers concise (under 300 words), practical, and culturally relevant for India.
Do NOT invent medical advice beyond what's in the excerpts."""


def _unique_sources(chunks: list[dict]) -> list[dict]:
    seen: set[str] = set()
    sources: list[dict] = []
    for chunk in chunks:
        slug = chunk["slug"]
        if slug in seen:
            continue
        seen.add(slug)
        sources.append({"title": chunk["title"], "slug": slug})
    return sources


def format_rag_response(
    answer: str,
    sources: list[dict],
    dietitian_slug: str,
) -> str:
    """Format grounded answer with article citations for WhatsApp."""
    lines = [answer.strip(), ""]
    if sources:
        lines.append("📚 *Sources:*")
        base = settings.FRONTEND_URL.rstrip("/")
        for source in sources:
            link = f"{base}/p/{dietitian_slug}/{source['slug']}"
            lines.append(f"• *{source['title']}*")
            lines.append(f"  {link}")
    return "\n".join(lines)


async def _generate_answer(question: str, chunks: list[dict]) -> str:
    context = "\n\n---\n\n".join(
        f"Article: {chunk['title']}\n{chunk['chunk_text']}" for chunk in chunks
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            (
                "human",
                "Article excerpts:\n{context}\n\nClient question: {question}",
            ),
        ]
    )
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHEAP_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        max_output_tokens=600,
    )
    chain = prompt | llm
    response = await chain.ainvoke({"context": context, "question": question})
    return str(response.content).strip()


async def answer_from_articles(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    dietitian_slug: str,
    question: str,
) -> str:
    """Embed question, retrieve chunks, and return a grounded WhatsApp-ready answer."""
    if not settings.GEMINI_API_KEY:
        return (
            "I can't look that up right now. "
            "Please ask your dietitian directly or check their articles online."
        )

    try:
        query_embedding = await embed_query(question)
        chunks = await search_relevant_chunks(
            db,
            dietitian_id,
            query_embedding,
            top_k=settings.RAG_TOP_K,
        )
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        return (
            "I had trouble searching your dietitian's articles. "
            "Please try again later or ask them directly."
        )

    if not chunks:
        return (
            "I couldn't find anything in your dietitian's published articles about that. "
            "Try asking your dietitian directly!"
        )

    filtered = [
        chunk for chunk in chunks if float(chunk.get("similarity") or 0) >= settings.RAG_MIN_SIMILARITY
    ]
    if not filtered:
        return (
            "I couldn't find a close match in your dietitian's articles. "
            "Please ask them directly for personalized advice."
        )

    try:
        answer = await _generate_answer(question, filtered)
    except Exception as exc:
        logger.error("RAG answer generation failed: %s", exc)
        return (
            "I found relevant articles but couldn't compose an answer right now. "
            "Please check the articles on your dietitian's page."
        )

    sources = _unique_sources(filtered)
    return format_rag_response(answer, sources, dietitian_slug)
