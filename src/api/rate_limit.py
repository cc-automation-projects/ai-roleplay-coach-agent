"""Rate limiting middleware — sliding window counter per client IP.

Applies configurable limits per endpoint pattern:
  - Default: 100 requests per 60-second window
  - Auth endpoints (``/api/v1/auth/*``): 10 requests per 60-second window
  - Metrics and health endpoints are excluded.

On each response the following headers are set:
  - ``X-RateLimit-Limit`` — max requests in the window
  - ``X-RateLimit-Remaining`` — remaining requests in the window
  - ``X-RateLimit-Reset`` — seconds until the window resets

When the limit is exceeded, a **429 Too Many Requests** response is returned
with a ``Retry-After`` header.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.requests import Request

if TYPE_CHECKING:
    from starlette.responses import Response
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger(__name__)

# Default configuration
DEFAULT_LIMIT: int = 100
DEFAULT_WINDOW: int = 60  # seconds
AUTH_LIMIT_VAL: int = 10
AUTH_WINDOW_VAL: int = 60  # seconds

EXCLUDED_PATHS: tuple[str, ...] = ("/metrics", "/health", "/ready")
AUTH_PATHS: tuple[str, ...] = ("/api/v1/auth",)

_CLEANUP_INTERVAL: int = 100


class RateLimitExceeded(Exception):  # noqa: N818
    """Raised when the client has exceeded the rate limit."""


class _SlidingWindowStore:
    """In-memory sliding-window counter per client key."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}
        self._request_count: int = 0

    def _cleanup(self) -> None:
        """Remove expired entries to prevent memory leak."""
        now = time.monotonic()
        oldest_window = now - 120
        expired_keys = [
            key
            for key, stamps in self._buckets.items()
            if stamps and stamps[-1] < oldest_window
        ]
        for key in expired_keys:
            del self._buckets[key]

    def check(self, key: str, limit: int, window: int) -> tuple[int, int]:
        """Check if *key* may proceed.

        Returns ``(remaining, reset_seconds)``.

        Raises *RateLimitExceeded* when the limit is exceeded.
        """
        self._request_count += 1
        if self._request_count % _CLEANUP_INTERVAL == 0:
            self._cleanup()

        now = time.monotonic()
        cutoff = now - window

        stamps = self._buckets.setdefault(key, [])
        while stamps and stamps[0] < cutoff:
            stamps.pop(0)

        if len(stamps) >= limit:
            raise RateLimitExceeded

        stamps.append(now)
        remaining = limit - len(stamps)
        reset_in_sec = int(window - (now - stamps[0])) if len(stamps) > 0 else window
        return remaining, max(reset_in_sec, 0)


_store = _SlidingWindowStore()


def _get_client_identifier(request: Request) -> str:
    """Extract a client identifier from the request."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    return f"rl:{client_ip}"


def _build_429_response(reset_seconds: int) -> Response:
    """Build a 429 Too Many Requests response."""
    return JSONResponse(
        status_code=429,
        content={
            "type": "about:blank",
            "title": "Too Many Requests",
            "status": 429,
            "detail": "Rate limit exceeded. Try again later.",
        },
        headers={"Retry-After": str(reset_seconds)},
    )


class RateLimitMiddleware:
    """ASGI middleware that enforces per-IP rate limits.

    Usage::

        app.add_middleware(RateLimitMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = DEFAULT_LIMIT,
        default_window: int = DEFAULT_WINDOW,
        auth_limit: int = AUTH_LIMIT_VAL,
        auth_window: int = AUTH_WINDOW_VAL,
    ) -> None:
        self.app = app
        self.default_limit = default_limit
        self.default_window = default_window
        self.auth_limit = auth_limit
        self.auth_window = auth_window

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope=scope, receive=receive)

        # Skip excluded paths
        path = request.url.path
        if any(path.startswith(ex) for ex in EXCLUDED_PATHS):
            await self.app(scope, receive, send)
            return

        # Determine limit for this endpoint
        if any(path.startswith(ap) for ap in AUTH_PATHS):
            limit = self.auth_limit
            window = self.auth_window
        else:
            limit = self.default_limit
            window = self.default_window

        # Enforce
        client_identifier = _get_client_identifier(request)
        try:
            remaining, reset_sec = _store.check(client_identifier, limit, window)
        except RateLimitExceeded:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_identifier,
                path=path,
                limit=limit,
                window=window,
            )
            response = _build_429_response(reset_seconds=window)
            await response(scope, receive, send)
            return

        # Inject rate-limit headers via send_wrapper
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                mh = MutableHeaders(scope=message)
                mh["X-RateLimit-Limit"] = str(limit)
                mh["X-RateLimit-Remaining"] = str(remaining)
                mh["X-RateLimit-Reset"] = str(reset_sec)
            await send(message)

        await self.app(scope, receive, send_wrapper)
