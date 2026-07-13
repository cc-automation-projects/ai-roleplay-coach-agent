"""Prometheus /metrics endpoint for observability.

Exposes:
- ``GET /api/v1/metrics`` — Prometheus text format (no auth required,
  intended for internal scrapers).

Middleware collects:
- Request counter (method, path, status)
- Request latency histogram
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

if TYPE_CHECKING:
    from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)

# ── Metrics definitions ─────────────────────────────────────────────

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ACTIVE_SESSIONS = Gauge("active_sessions", "Currently active coaching sessions")

TOTAL_EVALUATIONS = Counter("total_evaluations", "Total evaluations completed")

CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)",
    labelnames=["circuit"],
)

metrics_router = APIRouter()


@metrics_router.get("/api/v1/metrics")
async def metrics() -> Response:
    """Return Prometheus-formatted metrics (no auth for internal scraper)."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that records request count and latency."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start

        # Use the route template path (e.g. /api/v1/analyst/stats/{session_id})
        # to avoid cardinality explosion from dynamic path segments.
        path = self._resolve_route_path(request)
        method = request.method
        status = str(response.status_code)

        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)

        return response

    @staticmethod
    def _resolve_route_path(request: Request) -> str:
        """Return the route template path, or raw path as fallback."""
        route = request.scope.get("route")
        if route is not None:
            return getattr(route, "path", request.url.path)
        return request.url.path
