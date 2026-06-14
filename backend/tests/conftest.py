"""Shared test configuration and fixtures.

Patches PostgreSQL-specific column types (ARRAY, JSONB) to be SQLite-compatible
so tests can run without a PostgreSQL instance.
"""

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db


def _make_sqlite_compatible():
    """Register SQLite-compatible type compilation for PostgreSQL types."""
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    if not hasattr(SQLiteTypeCompiler, "visit_ARRAY"):
        SQLiteTypeCompiler.visit_ARRAY = lambda self, type_, **kw: "TEXT"

    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"


_make_sqlite_compatible()


@pytest_asyncio.fixture
async def client():
    """Create a test HTTP client with a fresh SQLite database."""
    from app.main import app

    # Each test gets a unique DB file
    db_file = f"test_{uuid.uuid4().hex[:8]}.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(db_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()

    # Cleanup
    if os.path.exists(db_file):
        os.remove(db_file)
