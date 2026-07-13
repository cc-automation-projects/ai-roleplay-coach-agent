"""Tests for CORS headers."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class TestCORS:
    BASE = "/api/v1"
    ORIGIN = "http://example.com"

    async def test_options_returns_cors_headers(
        self, async_client: httpx.AsyncClient
    ) -> None:
        headers = {"Origin": self.ORIGIN, "Access-Control-Request-Method": "GET"}
        resp = await async_client.options(f"{self.BASE}/auth/login", headers=headers)
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") in ("*", self.ORIGIN)
        assert "access-control-allow-methods" in resp.headers

    async def test_cors_header_on_normal_response(
        self, async_client: httpx.AsyncClient
    ) -> None:
        resp = await async_client.get("/health", headers={"Origin": self.ORIGIN})
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") in ("*", self.ORIGIN)
        assert resp.headers.get("access-control-allow-credentials") == "true"
