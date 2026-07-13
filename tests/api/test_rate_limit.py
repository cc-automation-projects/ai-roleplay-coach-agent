"""API tests for RateLimitMiddleware."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    import httpx

from api.rate_limit import _SlidingWindowStore


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    fresh = _SlidingWindowStore()
    with patch("api.rate_limit._store", fresh):
        yield


class TestRateLimitHeaders:
    async def test_headers_present(
        self, async_client: httpx.AsyncClient, auth_header: dict[str, str]
    ) -> None:
        resp = await async_client.get("/api/v1/gamification/leaderboard", headers=auth_header)
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers


class TestRateLimitEnforcement:
    """Uses public login endpoint to avoid auth_header/operator_user consumption."""
    @pytest.fixture(autouse=True)
    def _patch_low_limit(self) -> None:
        fresh = _SlidingWindowStore()
        original = _SlidingWindowStore.check
        def limited_check(self, key, limit, window):
            return original(self, key, 3, window)
        import types
        fresh.check = types.MethodType(limited_check, fresh)
        with patch("api.rate_limit._store", fresh):
            yield

    async def test_normal_request_succeeds(
        self, async_client: httpx.AsyncClient
    ) -> None:
        login = {"username": "x", "password": "y"}
        for _ in range(3):
            resp = await async_client.post("/api/v1/auth/login", json=login)
            assert resp.status_code == 401

    async def test_after_limit_returns_429(
        self, async_client: httpx.AsyncClient
    ) -> None:
        login = {"username": "x", "password": "y"}
        for _ in range(3):
            await async_client.post("/api/v1/auth/login", json=login)
        resp = await async_client.post("/api/v1/auth/login", json=login)
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    async def test_remaining_decreases(
        self, async_client: httpx.AsyncClient
    ) -> None:
        login = {"username": "x", "password": "y"}
        resp1 = await async_client.post("/api/v1/auth/login", json=login)
        r1 = int(resp1.headers["X-RateLimit-Remaining"])
        resp2 = await async_client.post("/api/v1/auth/login", json=login)
        r2 = int(resp2.headers["X-RateLimit-Remaining"])
        assert r2 == r1 - 1


class TestAuthEndpointStricterLimit:
    @pytest.fixture(autouse=True)
    def _patch_auth_limit(self) -> None:
        fresh = _SlidingWindowStore()
        original = _SlidingWindowStore.check
        def limited_check(self, key, limit, window):
            return original(self, key, 2, window)
        import types
        fresh.check = types.MethodType(limited_check, fresh)
        with patch("api.rate_limit._store", fresh):
            yield

    async def test_auth_limit_exceeded(
        self, async_client: httpx.AsyncClient
    ) -> None:
        login = {"username": "test", "password": "wrong"}
        r1 = await async_client.post("/api/v1/auth/login", json=login)
        assert r1.status_code == 401
        r2 = await async_client.post("/api/v1/auth/login", json=login)
        assert r2.status_code == 401
        r3 = await async_client.post("/api/v1/auth/login", json=login)
        assert r3.status_code == 429


class TestExcludedPaths:
    @pytest.fixture(autouse=True)
    def _patch_paths_limit(self) -> None:
        fresh = _SlidingWindowStore()
        original = _SlidingWindowStore.check
        def limited_check(self, key, limit, window):
            return original(self, key, 1, window)
        import types
        fresh.check = types.MethodType(limited_check, fresh)
        with patch("api.rate_limit._store", fresh):
            yield

    async def test_excluded_path_not_limited(
        self, async_client: httpx.AsyncClient
    ) -> None:
        await async_client.get("/api/v1/gamification/leaderboard")
        resp = await async_client.get("/health")
        assert resp.status_code == 200

    async def test_health_not_limited(
        self, async_client: httpx.AsyncClient
    ) -> None:
        await async_client.get("/api/v1/gamification/leaderboard")
        resp = await async_client.get("/health")
        assert resp.status_code == 200
