"""Tests for RFC 9457 Problem Details responses."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class TestProblemDetails:
    BASE = "/api/v1"
    JSON = "application/problem+json"

    async def test_missing_route_returns_problem(
        self, async_client: httpx.AsyncClient
    ) -> None:
        resp = await async_client.get("/api/v1/nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert body["title"] == "Not Found"
        assert body["status"] == 404
        assert "detail" in body
        assert "type" in body

    async def test_validation_error_returns_problem(
        self, async_client: httpx.AsyncClient
    ) -> None:
        resp = await async_client.post(
            f"{self.BASE}/auth/register",
            json={"bad_field": "value"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["title"] == "Validation Error"
        assert body["status"] == 422
        assert "errors" in body
        assert isinstance(body["errors"], list)

    async def test_auth_error_returns_problem(
        self, async_client: httpx.AsyncClient
    ) -> None:
        resp = await async_client.post(
            f"{self.BASE}/auth/login",
            json={"username": "nobody", "password": "wrong"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["title"] == "Unauthorized"
        assert body["status"] == 401

    async def test_health_still_works(
        self, async_client: httpx.AsyncClient
    ) -> None:
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
