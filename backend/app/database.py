"""Database connection and session management.

Uses SQLAlchemy 2.0 async engine with asyncpg driver.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_db():
    """FastAPI dependency that provides a database session per request."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
