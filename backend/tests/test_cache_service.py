"""Tests for Redis cache service (in-memory fallback when Redis unavailable)."""

import pytest

from app.services import cache_service


@pytest.mark.asyncio
async def test_cache_set_and_get():
    await cache_service.cache_set("test:key", {"value": 42}, ttl=60)
    result = await cache_service.cache_get("test:key")
    assert result == {"value": 42}


@pytest.mark.asyncio
async def test_cache_delete():
    await cache_service.cache_set("test:delete", {"x": 1}, ttl=60)
    await cache_service.cache_delete("test:delete")
    assert await cache_service.cache_get("test:delete") is None


def test_food_search_key_is_stable():
    k1 = cache_service.food_search_key("d1", "dal", None, True)
    k2 = cache_service.food_search_key("d1", "dal", None, True)
    k3 = cache_service.food_search_key("d1", "roti", None, True)
    assert k1 == k2
    assert k1 != k3
