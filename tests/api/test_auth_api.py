"""API tests for /api/v1/auth endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import httpx
    from fastapi import FastAPI


def _get_user_repo(app: FastAPI):
    """Pull the shared InMemoryUserRepository from overrides."""
    from api.dependencies import get_user_repo

    return app.dependency_overrides[get_user_repo]()


class TestAuthRegister:
    """POST /auth/register."""

    async def test_register_success(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/register with valid data → 201 + TokenPair."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "newbie", "password": "Secret123"},
        )
        assert resp.status_code == 201, f"Body: {resp.text}"
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "newbie"
        assert data["role"] == "operator"

    @pytest.mark.usefixtures("seeded_user")
    async def test_register_duplicate(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/register with existing username → 409."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "operator", "password": "Secret123"},
        )
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    async def test_register_short_password(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/register with short password → 422."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "newbie", "password": "short"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_username_short(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/register with short username -> 422."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "ab", "password": "Secret123"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_username_chars(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/register with invalid chars -> 422."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "user name!", "password": "Secret123"},
        )
        assert resp.status_code == 422


class TestAuthLogin:
    """POST /auth/login."""

    async def test_login_success(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register then login → 200 + TokenPair."""
        # Register first
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": "loginuser", "password": "Secret123"},
        )
        # Login
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "Secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/login with wrong password → 401."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": "user2", "password": "Secret123"},
        )
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "user2", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert "invalid" in resp.json()["detail"].lower()

    async def test_login_nonexistent(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/login with unknown user -> 401."""
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "Secret123"},
        )
        assert resp.status_code == 401

    async def test_login_inactive(
        self,
        async_client: httpx.AsyncClient,
        app: FastAPI,
    ) -> None:
        """POST /auth/login with deactivated user -> 401."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": "deact_user", "password": "Secret123"},
        )
        repo = _get_user_repo(app)
        user = await repo.get_by_username("deact_user")
        assert user is not None
        user.is_active = False
        await repo.update(user)

        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "deact_user", "password": "Secret123"},
        )
        assert resp.status_code == 401


class TestAuthRefresh:
    """POST /auth/refresh."""

    async def test_refresh_success(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register, login, refresh → new TokenPair."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": "refreshuser", "password": "Secret123"},
        )
        login_resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "refreshuser", "password": "Secret123"},
        )
        rt = login_resp.json()["refresh_token"]

        resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": rt},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """POST /auth/refresh with bogus token → 401."""
        resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "bogus.token.here"},
        )
        assert resp.status_code == 401


class TestAuthLogout:
    """POST /auth/logout."""

    async def test_logout(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register, login, logout → 200 + token revoked."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": "logoutuser", "password": "Secret123"},
        )
        login_resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "logoutuser", "password": "Secret123"},
        )
        rt = login_resp.json()["refresh_token"]

        resp = await async_client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": rt},
        )
        assert resp.status_code == 200

        # Using the same refresh token again should fail
        resp2 = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": rt},
        )
        assert resp2.status_code == 401


class TestAuthMe:
    """GET /auth/me."""

    async def test_me_success(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register, login, GET /me with Bearer token → user info."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": "meuser", "password": "Secret123"},
        )
        login_resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "meuser", "password": "Secret123"},
        )
        at = login_resp.json()["access_token"]

        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {at}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "meuser"
        assert data["role"] == "operator"
        assert data["is_active"] is True

    async def test_me_no_token(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """GET /auth/me without token → 401."""
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_bad_token(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """GET /auth/me with invalid token → 401."""
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer bogus.token.here"},
        )
        assert resp.status_code == 401
