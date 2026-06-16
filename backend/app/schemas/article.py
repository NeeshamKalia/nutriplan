"""Pydantic schemas for article management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreate(BaseModel):
    """Create a new article. Slug is auto-generated from title if omitted."""

    title: str = Field(..., min_length=1, max_length=500)
    slug: str | None = Field(None, max_length=200)
    summary: str | None = None
    content: str = Field(..., min_length=1)
    cover_image_url: str | None = None
    tags: list[str] | None = None
    status: str = Field(default="draft")
    meta_title: str | None = Field(None, max_length=200)
    meta_description: str | None = Field(None, max_length=300)


class ArticleUpdate(BaseModel):
    """Partial update — all fields optional."""

    title: str | None = Field(None, max_length=500)
    slug: str | None = Field(None, max_length=200)
    summary: str | None = None
    content: str | None = None
    cover_image_url: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    meta_title: str | None = Field(None, max_length=200)
    meta_description: str | None = Field(None, max_length=300)


class ArticleResponse(BaseModel):
    """Full article response."""

    id: str
    dietitian_id: str
    title: str
    slug: str
    summary: str | None = None
    content: str
    cover_image_url: str | None = None
    tags: list[str] | None = None
    status: str = "draft"
    meta_title: str | None = None
    meta_description: str | None = None
    published_at: datetime | None = None
    broadcasted_at: datetime | None = None
    broadcast_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Paginated article list."""

    articles: list[ArticleResponse]
    total: int


class ArticleBroadcastResponse(BaseModel):
    """Result of broadcasting an article to active clients via WhatsApp."""

    article: ArticleResponse
    sent_count: int
    failed_count: int
    skipped_count: int
    total_active_clients: int


class DietitianPublicProfile(BaseModel):
    """Public-facing dietitian profile for landing page."""

    id: str
    full_name: str
    slug: str
    bio: str | None = None
    photo_url: str | None = None
    specializations: list[str] | None = None
    qualifications: str | None = None
    practice_name: str | None = None
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)
