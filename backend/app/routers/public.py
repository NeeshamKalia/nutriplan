"""Public-facing endpoints — no authentication required.

Serves the dietitian landing page data and published articles.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.article import Article
from app.models.dietitian import Dietitian
from app.schemas.article import ArticleResponse, DietitianPublicProfile
from app.schemas.public import IntakeResponse, IntakeSubmit
from app.services import intake_service

router = APIRouter(prefix="/public", tags=["public"])


def _article_to_response(article: Article) -> ArticleResponse:
    """Inline conversion for public endpoints."""
    import json

    def _to_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            try:
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


def _dietitian_to_profile(d: Dietitian) -> DietitianPublicProfile:
    import json

    def _to_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            try:
                return json.loads(val)
            except (ValueError, TypeError):
                return [s.strip() for s in val.split(",")]
        return None

    return DietitianPublicProfile(
        id=str(d.id),
        full_name=d.full_name,
        slug=d.slug,
        bio=d.bio,
        photo_url=d.photo_url,
        specializations=_to_list(d.specializations),
        qualifications=d.qualifications,
        practice_name=d.practice_name,
        phone=d.phone,
    )


@router.get("/dietitians/{slug}", response_model=DietitianPublicProfile)
async def get_dietitian_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a dietitian's public profile by slug."""
    result = await db.execute(
        select(Dietitian).where(Dietitian.slug == slug, Dietitian.is_active)
    )
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(status_code=404, detail="Dietitian not found")
    return _dietitian_to_profile(dietitian)


@router.get("/dietitians/{slug}/articles", response_model=list[ArticleResponse])
async def get_public_articles(slug: str, db: AsyncSession = Depends(get_db)):
    """Get published articles for a dietitian's landing page."""
    result = await db.execute(
        select(Dietitian).where(Dietitian.slug == slug, Dietitian.is_active)
    )
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(status_code=404, detail="Dietitian not found")

    stmt = (
        select(Article)
        .where(Article.dietitian_id == dietitian.id, Article.status == "published")
        .order_by(Article.published_at.desc())
    )
    result = await db.execute(stmt)
    return [_article_to_response(a) for a in result.scalars().all()]


@router.get(
    "/dietitians/{dietitian_slug}/articles/{article_slug}",
    response_model=ArticleResponse,
)
async def get_public_article(
    dietitian_slug: str, article_slug: str, db: AsyncSession = Depends(get_db)
):
    """Get a single published article by slugs."""
    result = await db.execute(
        select(Dietitian).where(
            Dietitian.slug == dietitian_slug, Dietitian.is_active
        )
    )
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(status_code=404, detail="Dietitian not found")

    result = await db.execute(
        select(Article).where(
            Article.dietitian_id == dietitian.id,
            Article.slug == article_slug,
            Article.status == "published",
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return _article_to_response(article)


@router.post(
    "/dietitians/{slug}/intake",
    response_model=IntakeResponse,
    status_code=201,
)
async def submit_intake_form(
    slug: str, data: IntakeSubmit, db: AsyncSession = Depends(get_db)
):
    """Submit a new client intake form from the landing page."""
    return await intake_service.submit_intake(db, slug, data)
