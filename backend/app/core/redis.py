"""Async Redis client with graceful fallback when Redis is unavailable."""

from redis.asyncio import Redis

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_redis: Redis | None = None
_redis_checked = False


async def get_redis() -> Redis | None:
    """Return a shared Redis connection, or None if Redis is disabled/unreachable."""
    global _redis, _redis_checked
    if not settings.REDIS_URL or not settings.REDIS_ENABLED:
        return None
    if _redis_checked:
        return _redis

    _redis_checked = True
    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        _redis = client
        logger.info("Redis connected")
    except Exception as exc:
        logger.warning("Redis unavailable — caching disabled: %s", exc)
        _redis = None
    return _redis


async def close_redis() -> None:
    global _redis, _redis_checked
    if _redis is not None:
        await _redis.aclose()
    _redis = None
    _redis_checked = False
