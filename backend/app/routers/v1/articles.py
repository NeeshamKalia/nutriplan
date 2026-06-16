"""Authenticated article management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.article import (
    ArticleBroadcastResponse,
    ArticleCreate,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)
from app.services import article_service

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("", response_model=ArticleResponse, status_code=201)
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.create_article(db, current_user.id, data)


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    status: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.list_articles(
        db, current_user.id, article_status=status, search=search
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.get_article(db, current_user.id, article_id)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.update_article(db, current_user.id, article_id, data)


@router.post("/{article_id}/publish", response_model=ArticleResponse)
async def publish_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.publish_article(db, current_user.id, article_id)


@router.post("/{article_id}/unpublish", response_model=ArticleResponse)
async def unpublish_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.unpublish_article(db, current_user.id, article_id)


@router.post("/{article_id}/broadcast", response_model=ArticleBroadcastResponse)
async def broadcast_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await article_service.broadcast_article(db, current_user.id, article_id)


@router.delete("/{article_id}")
async def delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    await article_service.delete_article(db, current_user.id, article_id)
    return {"status": "deleted"}
