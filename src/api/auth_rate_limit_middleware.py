from __future__ import annotations

import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.types import ASGIApp

# Rules: path_prefix, limit, window_seconds, block_seconds
DEFAULT_AUTH_RULES = [
    {"path_prefix": "/api/v1/auth/register", "limit": 5, "window": 600, "block": 1800},
    {"path_prefix": "/api/v1/auth/login", "limit": 10, "window": 600, "block": 1800},
    {"path_prefix": "/api/v1/auth/refresh", "limit": 20, "window": 600, "block": 1800},
    {"path_prefix": "/api/v1/auth", "limit": 20, "window": 600, "block": 1800},  # fallback
]

# Shared store (module-level so tests can reset it without lazy-init issues)
_AUTH_STORE: dict[str, tuple[int, float, float]] = {}


def reset_auth_rate_limit_store() -> None:
    """Clear shared auth rate limit store (for test isolation)."""
    _AUTH_STORE.clear()


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rules: list[dict] | None = None) -> None:
        super().__init__(app)
        self.rules = rules or DEFAULT_AUTH_RULES

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        rule = None
        for r in self.rules:
            if path.startswith(r["path_prefix"]):
                rule = r
                break
        if rule is None:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{rule['path_prefix']}"
        now = time.time()

        count, first_ts, block_until = _AUTH_STORE.get(key, (0, now, 0.0))

        # Check if blocked
        if block_until > now:
            retry_after = int(block_until - now)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Blocked for {retry_after} seconds."},
                headers={"Retry-After": str(retry_after)},
            )

        # Reset if window expired
        if now - first_ts > rule["window"]:
            count = 0
            first_ts = now

        if count >= rule["limit"]:
            # Exceeded, set block
            block_until = now + rule["block"]
            _AUTH_STORE[key] = (count, first_ts, block_until)
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Blocked for {rule['block']} seconds."},
                headers={"Retry-After": str(rule["block"])},
            )

        # Increment count
        _AUTH_STORE[key] = (count + 1, first_ts, 0.0)

        response = await call_next(request)
        # Add rate-limit headers
        response.headers["X-RateLimit-Limit"] = str(rule["limit"])
        remaining = rule["limit"] - (count + 1)
        response.headers["X-RateLimit-Remaining"] = str(max(remaining, 0))
        response.headers["X-RateLimit-Reset"] = str(int(rule["window"] - (now - first_ts)))
        return response
