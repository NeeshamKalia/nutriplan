"""Lightweight in-memory rate limiter middleware.

SEC-003: Protects auth endpoints from brute-force and registration spam.
Uses a fixed-window counter per IP without external dependencies (no Redis
required until Phase 10+).

Algorithm: Fixed Window
  Each IP gets a counter that resets after the window expires.
  Example: login at 5/60s means at most 5 requests in any 60-second window.

Configured limits:
  - POST /api/v1/auth/login    → max 5 requests per 60-second window per IP
  - POST /api/v1/auth/register → max 3 requests per 3600-second (1hr) window per IP
  - POST /api/v1/auth/refresh  → max 10 requests per 60-second window per IP
  - POST /api/v1/public/*      → max 5 requests per 3600-second (1hr) window per IP
"""

import time
from typing import NamedTuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import get_logger

logger = get_logger(__name__)

MAX_BUCKETS = 10000  # Prevent memory exhaustion from IP churn


class RateLimit(NamedTuple):
    max_requests: int
    window_seconds: int


# Path prefix → rate limit config
RATE_LIMITS: dict[str, RateLimit] = {
    "/api/v1/auth/login": RateLimit(5, 60),
    "/api/v1/auth/register": RateLimit(3, 3600),
    "/api/v1/auth/refresh": RateLimit(10, 60),
}

# Prefix match for public endpoints
PUBLIC_RATE_LIMIT = RateLimit(5, 3600)
PUBLIC_PREFIX = "/api/v1/public/"


class _FixedWindow:
    """Fixed-window counter: resets count after window_seconds elapse."""

    __slots__ = ("count", "window_start")

    def __init__(self):
        self.count = 0
        self.window_start = time.monotonic()


# Global state: {(path, ip): _FixedWindow}
_windows: dict[tuple[str, str], _FixedWindow] = {}


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _resolve_limit(path: str, method: str) -> RateLimit | None:
    """Find the applicable rate limit for this request."""
    if method != "POST":
        return None

    # Exact path match
    limit = RATE_LIMITS.get(path)
    if limit:
        return limit

    # Prefix match for public intake form
    if path.startswith(PUBLIC_PREFIX):
        return PUBLIC_RATE_LIMIT

    return None


def _check_rate_limit(key: tuple[str, str], limit: RateLimit) -> bool:
    """Return True if the request is allowed, False if rate-limited.

    Uses fixed-window algorithm: counter resets when window expires.
    """
    now = time.monotonic()

    # Evict stale windows to bound memory
    if len(_windows) > MAX_BUCKETS:
        stale_keys = [
            k for k, w in _windows.items()
            if now - w.window_start > max(7200, limit.window_seconds * 2)
        ]
        for k in stale_keys:
            _windows.pop(k, None)

    window = _windows.get(key)

    if window is None:
        # First request from this IP for this path
        window = _FixedWindow()
        _windows[key] = window

    # Check if the current window has expired → reset
    if now - window.window_start >= limit.window_seconds:
        window.count = 0
        window.window_start = now

    # Check if under limit
    if window.count < limit.max_requests:
        window.count += 1
        return True

    return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces per-IP rate limits on auth/public endpoints."""

    async def dispatch(self, request: Request, call_next):
        limit = _resolve_limit(request.url.path, request.method)
        if limit is None:
            return await call_next(request)

        ip = _get_client_ip(request)
        key = (request.url.path, ip)

        if not _check_rate_limit(key, limit):
            logger.warning(
                "Rate limit exceeded: %s from %s on %s",
                request.method,
                ip,
                request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                },
                headers={"Retry-After": str(limit.window_seconds)},
            )

        return await call_next(request)
