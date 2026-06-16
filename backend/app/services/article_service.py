"""Article management service — CRUD with multi-tenant isolation.

Every query filters by dietitian_id. A dietitian must NEVER
see another dietitian's articles.
"""

import asyncio
import re
import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logger import get_logger
from app.models.article import Article
from app.models.client import Client
from app.models.dietitian import Dietitian
from app.schemas.article import (
    ArticleBroadcastResponse,
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from app.services import article_embedding_service
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.message_formatter import format_article_broadcast

logger = get_logger(__name__)


async def _sync_article_index(db: AsyncSession, article: Article) -> None:
    """Index or remove embeddings when article publish state changes."""
    try:
        if article.status == "published":
            await article_embedding_service.index_article(db, article)
        else:
            await article_embedding_service.delete_article_embeddings(db, article.id)
    except Exception as exc:
        logger.warning(
            "Article RAG indexing failed",
            extra={"article_id": str(article.id), "error": str(exc)},
        )


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:200]


def _article_to_response(article: Article) -> ArticleResponse:
    """Convert an Article model to a response schema."""

    def _to_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            try:
                import json
                return json.loads(val)
            except (ValueError, TypeError):
                return [s.strip() for s in val.split(",")]
        return None

    return ArticleResponse(
        id=str(article.id),
        dietitian_id=str(article.dietitian_id),
        title=article.title,
        slug=article.slug,
        summary=article.summary,
        content=article.content,
        cover_image_url=article.cover_image_url,
        tags=_to_list(article.tags),
        status=article.status or "draft",
        meta_title=article.meta_title,
        meta_description=article.meta_description,
        published_at=article.published_at,
        broadcasted_at=article.broadcasted_at,
        broadcast_count=article.broadcast_count or 0,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


async def _ensure_unique_slug(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    slug: str,
    exclude_id: uuid_mod.UUID | None = None,
) -> str:
    """Ensure slug is unique per dietitian; append -2, -3, etc. if needed."""
    base_slug = slug
    counter = 1
    while True:
        query = select(Article).where(
            Article.dietitian_id == dietitian_id,
            Article.slug == slug,
        )
        if exclude_id:
            query = query.where(Article.id != exclude_id)
        result = await db.execute(query)
        if not result.scalar_one_or_none():
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"


async def create_article(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, data: ArticleCreate
) -> ArticleResponse:
    """Create a new article with auto-generated slug if not provided."""
    slug = data.slug if data.slug else _slugify(data.title)
    slug = await _ensure_unique_slug(db, dietitian_id, slug)

    article = Article(
        dietitian_id=dietitian_id,
        title=data.title,
        slug=slug,
        summary=data.summary,
        content=data.content,
        cover_image_url=data.cover_image_url,
        tags=data.tags,
        status=data.status,
        meta_title=data.meta_title,
        meta_description=data.meta_description,
    )

    if data.status == "published":
        article.published_at = datetime.now(timezone.utc)

    db.add(article)
    await db.commit()
    await db.refresh(article)
    await _sync_article_index(db, article)

    logger.info(
        "Article created",
        extra={"article_id": str(article.id), "dietitian_id": str(dietitian_id)},
    )
    return _article_to_response(article)


async def list_articles(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    article_status: str | None = None,
    search: str | None = None,
) -> ArticleListResponse:
    """List articles for a dietitian with optional filters."""
    base_query = select(Article).where(Article.dietitian_id == dietitian_id)

    if article_status:
        base_query = base_query.where(Article.status == article_status)

    if search:
        search_term = f"%{search}%"
        base_query = base_query.where(Article.title.ilike(search_term))

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = base_query.order_by(Article.created_at.desc())
    result = await db.execute(query)
    articles = result.scalars().all()

    return ArticleListResponse(
        articles=[_article_to_response(a) for a in articles],
        total=total,
    )


async def get_article(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, article_id: uuid_mod.UUID
) -> ArticleResponse:
    """Get a single article, enforcing tenant isolation."""
    result = await db.execute(
        select(Article).where(
            Article.id == article_id,
            Article.dietitian_id == dietitian_id,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    return _article_to_response(article)


async def update_article(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    article_id: uuid_mod.UUID,
    data: ArticleUpdate,
) -> ArticleResponse:
    """Partially update an article."""
    result = await db.execute(
        select(Article).where(
            Article.id == article_id,
            Article.dietitian_id == dietitian_id,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "slug" in update_data and update_data["slug"] != article.slug:
        update_data["slug"] = await _ensure_unique_slug(
            db, dietitian_id, update_data["slug"], exclude_id=article.id
        )

    if (
        "status" in update_data
        and update_data["status"] == "published"
        and article.status != "published"
    ):
        article.published_at = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(article, key, value)

    await db.commit()
    await db.refresh(article)
    await _sync_article_index(db, article)

    logger.info(
        "Article updated",
        extra={"article_id": str(article_id), "dietitian_id": str(dietitian_id)},
    )
    return _article_to_response(article)


async def publish_article(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, article_id: uuid_mod.UUID
) -> ArticleResponse:
    """Publish an article (set status='published' and published_at)."""
    result = await db.execute(
        select(Article).where(
            Article.id == article_id,
            Article.dietitian_id == dietitian_id,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    article.status = "published"
    if not article.published_at:
        article.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(article)
    await _sync_article_index(db, article)
    return _article_to_response(article)


async def unpublish_article(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, article_id: uuid_mod.UUID
) -> ArticleResponse:
    """Unpublish an article (revert to draft)."""
    result = await db.execute(
        select(Article).where(
            Article.id == article_id,
            Article.dietitian_id == dietitian_id,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    article.status = "draft"
    await db.commit()
    await db.refresh(article)
    await _sync_article_index(db, article)
    return _article_to_response(article)


async def delete_article(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, article_id: uuid_mod.UUID
) -> None:
    """Hard-delete an article."""
    result = await db.execute(
        select(Article).where(
            Article.id == article_id,
            Article.dietitian_id == dietitian_id,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    await db.delete(article)
    await db.commit()

    logger.info(
        "Article deleted",
        extra={"article_id": str(article_id), "dietitian_id": str(dietitian_id)},
    )


# ~20 msgs/sec — well under Meta's 80/sec limit
_BROADCAST_SEND_DELAY_SEC = 0.05


async def broadcast_article(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, article_id: uuid_mod.UUID
) -> ArticleBroadcastResponse:
    """Send a published article summary to all active clients via WhatsApp."""
    result = await db.execute(
        select(Article).where(
            Article.id == article_id,
            Article.dietitian_id == dietitian_id,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    if article.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published articles can be broadcast",
        )

    dietitian_result = await db.execute(
        select(Dietitian).where(Dietitian.id == dietitian_id)
    )
    dietitian = dietitian_result.scalar_one()

    clients_result = await db.execute(
        select(Client).where(
            Client.dietitian_id == dietitian_id,
            Client.status == "active",
        )
    )
    clients = clients_result.scalars().all()

    article_link = (
        f"{settings.FRONTEND_URL.rstrip('/')}/p/{dietitian.slug}/{article.slug}"
    )
    message = format_article_broadcast(
        dietitian_name=dietitian.full_name,
        title=article.title,
        summary=article.summary,
        article_link=article_link,
    )

    sent_count = 0
    failed_count = 0
    skipped_count = 0

    for client in clients:
        to_number = (client.whatsapp_number or "").strip()
        if not to_number:
            skipped_count += 1
            continue

        result_data = await whatsapp_service.send_text_message(
            to_number=to_number,
            body=message,
            db=db,
            client_id=client.id,
            dietitian_id=dietitian_id,
        )
        if result_data:
            sent_count += 1
        else:
            failed_count += 1

        await asyncio.sleep(_BROADCAST_SEND_DELAY_SEC)

    article.broadcasted_at = datetime.now(timezone.utc)
    article.broadcast_count = (article.broadcast_count or 0) + sent_count
    await db.commit()
    await db.refresh(article)

    logger.info(
        "Article broadcast complete",
        extra={
            "article_id": str(article_id),
            "dietitian_id": str(dietitian_id),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
        },
    )

    return ArticleBroadcastResponse(
        article=_article_to_response(article),
        sent_count=sent_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        total_active_clients=len(clients),
    )
