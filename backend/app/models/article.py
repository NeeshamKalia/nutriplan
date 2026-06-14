"""SQLAlchemy models for articles and article embeddings."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Article(Base):
    """Blog article written by a dietitian for their landing page.

    Articles can be broadcast to clients via WhatsApp template messages.
    Published articles are indexed for RAG-based Q&A.
    """

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dietitian_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dietitians.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(500), nullable=False)
    slug = Column(String(200), nullable=False)
    summary = Column(Text)
    content = Column(Text, nullable=False)
    cover_image_url = Column(Text)

    tags = Column(ARRAY(Text))

    status = Column(String(20), default="draft")
    published_at = Column(DateTime(timezone=True))

    # SEO
    meta_title = Column(String(200))
    meta_description = Column(String(300))

    # WhatsApp broadcast
    broadcasted_at = Column(DateTime(timezone=True))
    broadcast_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    dietitian = relationship("Dietitian", back_populates="articles")
    embeddings = relationship(
        "ArticleEmbedding", back_populates="article", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("dietitian_id", "slug", name="uq_article_slug"),
    )


class ArticleEmbedding(Base):
    """Chunked text embeddings for RAG-based article Q&A.

    Uses pgvector for similarity search. Embedding dimension matches
    the configured embedding model (1536 for text-embedding-3-small,
    768 for Gemini text-embedding-004).
    """

    __tablename__ = "article_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
    )

    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    # Note: vector column is added via raw SQL in migration since
    # SQLAlchemy doesn't natively support pgvector column types.
    # The migration will add: embedding vector(768)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    article = relationship("Article", back_populates="embeddings")
