"""Shared test configuration and fixtures.

QA-001 FIX: When DATABASE_URL env var is set (e.g. in CI), tests run against
PostgreSQL directly — no patching needed. When DATABASE_URL is not set
(local dev without PostgreSQL), falls back to SQLite with ARRAY/JSONB patching.

This ensures CI actually tests against the real database engine.
"""

import json
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db

# Import all models so they are registered with Base before patching
import app.models  # noqa: F401

# ── Speed: use fast bcrypt rounds in tests ─────────────────────────
# Default bcrypt rounds=12 takes ~250ms per hash. With 142 tests
# registering dietitians, that adds 30-60+ seconds of pure hashing.
# Minimum rounds=4 cuts each hash to ~1ms.
from app.utils.security import pwd_context
pwd_context.update(schemes=["bcrypt"], bcrypt__rounds=4)

# Detect whether we have a real PostgreSQL URL
_CI_DATABASE_URL = os.environ.get("DATABASE_URL")
_USE_POSTGRES = bool(_CI_DATABASE_URL and "postgresql" in _CI_DATABASE_URL)


class JSONEncodedList(TypeDecorator):
    """Stores Python list as JSON-encoded TEXT for SQLite compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return value


class JSONEncodedDict(TypeDecorator):
    """Stores Python dict/list as JSON-encoded TEXT for SQLite compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return value


def _make_sqlite_compatible():
    """Patch all ARRAY/JSONB columns in all models to use JSON-serializing types.

    Only applied when running against SQLite (local dev without PostgreSQL).
    """
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    if not hasattr(SQLiteTypeCompiler, "visit_ARRAY"):
        SQLiteTypeCompiler.visit_ARRAY = lambda self, type_, **kw: "TEXT"
    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):
        SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"

    # Patch each Column's type in the Table metadata
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, ARRAY):
                col.type = JSONEncodedList()
            elif isinstance(col.type, JSONB):
                col.type = JSONEncodedDict()


# Only apply SQLite patching when NOT using PostgreSQL
if not _USE_POSTGRES:
    _make_sqlite_compatible()



@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter state between tests to prevent 429 cascades."""
    from app.core.rate_limiter import _windows
    _windows.clear()
    yield
    _windows.clear()


@pytest.fixture(autouse=True)
def mock_article_embeddings(monkeypatch):
    """Mock embedding service globally — tests should never call real AI APIs."""
    from app.services import article_embedding_service

    async def _noop_index(db, article):
        return 0

    async def _noop_delete(db, article_id):
        pass

    monkeypatch.setattr(article_embedding_service, "index_article", _noop_index)
    monkeypatch.setattr(article_embedding_service, "delete_article_embeddings", _noop_delete)


@pytest_asyncio.fixture
async def client():
    """Create a test HTTP client with a fresh database.

    Uses PostgreSQL when DATABASE_URL is set (CI), SQLite otherwise (local dev).
    """
    from app.main import app

    if _USE_POSTGRES:
        # CI: Use real PostgreSQL — create tables, run tests, drop tables
        engine = create_async_engine(_CI_DATABASE_URL, echo=False)
    else:
        # Local dev: Use ephemeral SQLite file
        db_file = f"test_{uuid.uuid4().hex[:8]}.db"
        db_url = f"sqlite+aiosqlite:///{db_file}"
        engine = create_async_engine(db_url, echo=False)

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

    if _USE_POSTGRES:
        # CI: Drop all tables after test (clean state for next run)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    if not _USE_POSTGRES:
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
        except PermissionError:
            pass
