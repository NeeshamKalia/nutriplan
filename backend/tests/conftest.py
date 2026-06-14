"""Shared test configuration and fixtures.

Patches PostgreSQL-specific column types (ARRAY, JSONB) to be SQLite-compatible.

Strategy: Replace the `type` attribute on Column objects in the Table metadata
before any sessions are created. This ensures SQLite gets JSON-encoded TEXT
for ARRAY/JSONB columns.
"""

import json
import os
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Text, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db

# Import all models so they are registered with Base before patching
import app.models  # noqa: F401


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
    """Patch all ARRAY/JSONB columns in all models to use JSON-serializing types."""
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


_make_sqlite_compatible()


@pytest_asyncio.fixture
async def client():
    """Create a test HTTP client with a fresh SQLite database."""
    from app.main import app

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
    await engine.dispose()

    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except PermissionError:
        pass
