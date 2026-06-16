"""Redis-backed response cache with in-memory fallback for tests."""

import hashlib
import json
import time
from typing import Any

from app.config import settings
from app.core.logger import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)

_memory_cache: dict[str, tuple[float, str]] = {}


def _ttl() -> int:
    return settings.CACHE_TTL_SECONDS


def food_search_key(
    dietitian_id: str,
    q: str | None,
    category: str | None,
    is_vegetarian: bool | None,
) -> str:
    raw = f"{q or ''}|{category or ''}|{is_vegetarian}"
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"foods:search:{dietitian_id}:{digest}"


def client_profile_key(dietitian_id: str, client_id: str) -> str:
    return f"client:profile:{dietitian_id}:{client_id}"


def food_fetch_key(dietitian_id: str) -> str:
    return f"foods:fetch:{dietitian_id}"


async def cache_get(key: str) -> Any | None:
    redis = await get_redis()
    if redis:
        try:
            raw = await redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.debug("Redis cache get failed for %s: %s", key, exc)

    entry = _memory_cache.get(key)
    if not entry:
        return None
    expires_at, raw = entry
    if time.time() > expires_at:
        _memory_cache.pop(key, None)
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    ttl = ttl or _ttl()
    raw = json.dumps(value, default=str)

    redis = await get_redis()
    if redis:
        try:
            await redis.set(key, raw, ex=ttl)
            return
        except Exception as exc:
            logger.debug("Redis cache set failed for %s: %s", key, exc)

    _memory_cache[key] = (time.time() + ttl, raw)


async def cache_delete(key: str) -> None:
    redis = await get_redis()
    if redis:
        try:
            await redis.delete(key)
        except Exception as exc:
            logger.debug("Redis cache delete failed for %s: %s", key, exc)
    _memory_cache.pop(key, None)


async def cache_delete_prefix(prefix: str) -> None:
    redis = await get_redis()
    if redis:
        try:
            keys = [key async for key in redis.scan_iter(match=f"{prefix}*")]
            if keys:
                await redis.delete(*keys)
        except Exception as exc:
            logger.debug("Redis cache prefix delete failed for %s: %s", prefix, exc)

    for key in list(_memory_cache.keys()):
        if key.startswith(prefix):
            _memory_cache.pop(key, None)
