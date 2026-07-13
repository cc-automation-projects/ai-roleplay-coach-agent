"""Tests for the /health endpoint."""

import httpx


class TestHealth:
    """Health and readiness endpoint tests."""

    async def test_health_ok(self, async_client: httpx.AsyncClient) -> None:
        """Health endpoint returns 200 with expected fields."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "uptime_seconds" in data

    async def test_ready_ok(self, async_client: httpx.AsyncClient) -> None:
        """Ready endpoint returns 200 with components."""
        response = await async_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "components" in data
        assert data["components"]["auth"] == "ok"
        assert data["components"]["coach"] == "ok"
