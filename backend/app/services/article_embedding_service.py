"""Article embedding index for RAG — chunk, embed, store in pgvector."""

import uuid as uuid_mod

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_texts
from app.ai.text_utils import chunk_text, strip_html
from app.core.logger import get_logger
from app.models.article import Article, ArticleEmbedding

logger = get_logger(__name__)


def _article_index_text(article: Article) -> str:
    """Combine article fields into indexable plain text."""
    parts = [article.title or ""]
    if article.summary:
        parts.append(article.summary)
    if article.content:
        parts.append(strip_html(article.content))
    return "\n\n".join(p for p in parts if p.strip())


def _vector_to_pg(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


async def delete_article_embeddings(db: AsyncSession, article_id: uuid_mod.UUID) -> None:
    """Remove all embedding chunks for an article."""
    await db.execute(
        delete(ArticleEmbedding).where(ArticleEmbedding.article_id == article_id)
    )
    await db.commit()


async def index_article(db: AsyncSession, article: Article) -> int:
    """Chunk article text, embed, and store vectors. Returns chunk count."""
    await delete_article_embeddings(db, article.id)

    index_text = _article_index_text(article)
    chunks = chunk_text(index_text)
    if not chunks:
        logger.info("No chunks to index for article %s", article.id)
        return 0

    vectors = await embed_texts(chunks)

    for chunk_index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        row_id = uuid_mod.uuid4()
        await db.execute(
            text(
                """
                INSERT INTO article_embeddings
                    (id, article_id, chunk_text, chunk_index, embedding)
                VALUES
                    (:id, :article_id, :chunk_text, :chunk_index, CAST(:embedding AS vector))
                """
            ),
            {
                "id": row_id,
                "article_id": article.id,
                "chunk_text": chunk,
                "chunk_index": chunk_index,
                "embedding": _vector_to_pg(vector),
            },
        )

    await db.commit()
    logger.info(
        "Indexed article for RAG",
        extra={"article_id": str(article.id), "chunk_count": len(chunks)},
    )
    return len(chunks)


async def search_relevant_chunks(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    query_embedding: list[float],
    top_k: int = 3,
) -> list[dict]:
    """Find the most similar published article chunks for a dietitian."""
    vector_str = _vector_to_pg(query_embedding)
    result = await db.execute(
        text(
            """
            SELECT
                ae.chunk_text,
                ae.chunk_index,
                a.title,
                a.slug,
                1 - (ae.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM article_embeddings ae
            JOIN articles a ON a.id = ae.article_id
            WHERE a.dietitian_id = :dietitian_id
              AND a.status = 'published'
            ORDER BY ae.embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
            """
        ),
        {
            "query_vec": vector_str,
            "dietitian_id": dietitian_id,
            "top_k": top_k,
        },
    )
    rows = result.mappings().all()
    return [dict(row) for row in rows]
