"""E2E: Auth flow — register, login, refresh, logout, me.

Tests token lifecycle and user identification through HTTP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import httpx


pytestmark = [pytest.mark.asyncio]


class TestAuthFlow:
    """Full auth token lifecycle via HTTP."""

    BASE = "/api/v1/auth"

    async def _register(
        self, client: httpx.AsyncClient, name: str, pw: str = "Secret123"
    ) -> dict:
        resp = await client.post(
            f"{self.BASE}/register",
            json={"username": name, "password": pw},
        )
        assert resp.status_code == 201, f"Register failed: {resp.text}"
        return resp.json()

    async def test_register_and_me(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register → GET /me with token → user info."""
        data = await self._register(async_client, "auth_e2e_me")
        resp = await async_client.get(
            f"{self.BASE}/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert resp.status_code == 200
        me = resp.json()
        assert me["username"] == "auth_e2e_me"
        assert me["role"] == "operator"
        assert me["is_active"] is True

    async def test_login_then_refresh(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register → login → refresh → new tokens work."""
        uname = "auth_e2e_refresh"
        pw = "Secret123"
        await self._register(async_client, uname, pw)

        # Login
        login = await async_client.post(
            f"{self.BASE}/login",
            json={"username": uname, "password": pw},
        )
        assert login.status_code == 200
        tokens = login.json()
        old_rt = tokens["refresh_token"]

        # Refresh
        refresh = await async_client.post(
            f"{self.BASE}/refresh",
            json={"refresh_token": old_rt},
        )
        assert refresh.status_code == 200
        new_tokens = refresh.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

        # Refreshed token works for /me
        me = await async_client.get(
            f"{self.BASE}/me",
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["username"] == uname

    async def test_logout_revokes_refresh(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Register → login → logout → old refresh token rejected."""
        uname = "auth_e2e_logout"
        pw = "Secret123"
        await self._register(async_client, uname, pw)

        login = await async_client.post(
            f"{self.BASE}/login",
            json={"username": uname, "password": pw},
        )
        assert login.status_code == 200
        rt = login.json()["refresh_token"]

        # Logout
        logout = await async_client.post(
            f"{self.BASE}/logout",
            json={"refresh_token": rt},
        )
        assert logout.status_code == 200

        # Old refresh token rejected
        re_refresh = await async_client.post(
            f"{self.BASE}/refresh",
            json={"refresh_token": rt},
        )
        assert re_refresh.status_code == 401

    async def test_invalid_tokens_rejected(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Bogus tokens are rejected with 401."""
        # Invalid access token
        me = await async_client.get(
            f"{self.BASE}/me",
            headers={"Authorization": "Bearer eyJ.invalid.token"},
        )
        assert me.status_code == 401

        # Invalid refresh token
        refresh = await async_client.post(
            f"{self.BASE}/refresh",
            json={"refresh_token": "bogus.refresh.token"},
        )
        assert refresh.status_code == 401

    async def test_no_token_returns_401(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Endpoints without auth → 401."""
        me = await async_client.get(f"{self.BASE}/me")
        assert me.status_code == 401
