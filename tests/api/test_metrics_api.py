"""Tests for the Prometheus /metrics endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class TestMetricsAPI:
    """GET /api/v1/metrics should expose Prometheus text."""

    async def test_metrics_returns_200(self, async_client: httpx.AsyncClient) -> None:
        """Metrics endpoint returns 200 with text content type."""
        response = await async_client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/plain")

    async def test_metrics_contains_counters(self, async_client: httpx.AsyncClient) -> None:
        """After a request, counter data is present."""
        await async_client.get("/health")
        resp = await async_client.get("/api/v1/metrics")
        body = resp.text
        assert "http_requests_total" in body
        assert "/health" in body

    async def test_metrics_accessible_without_auth(self, async_client: httpx.AsyncClient) -> None:
        """Metrics endpoint does not require authentication."""
        response = await async_client.get("/api/v1/metrics")
        assert response.status_code == 200

    async def test_metrics_contains_latency_histogram(self, async_client: httpx.AsyncClient) -> None:
        """Latency histogram is registered."""
        resp = await async_client.get("/api/v1/metrics")
        assert "http_request_duration_seconds" in resp.text
