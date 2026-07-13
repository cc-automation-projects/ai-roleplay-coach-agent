"""E2E: RBAC role enforcement across all API endpoints via HTTP.

Tests that role gates work end-to-end:
  - operator accessing trainer-only endpoints → 403
  - admin bypassing any role gate → 200
  - unauthorized requests → 401
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    import httpx

    from infrastructure.memory.repositories import InMemoryUserRepository


pytestmark = [pytest.mark.asyncio]


async def _create_user_with_role(
    user_repo: InMemoryUserRepository,
    role_name: str,
    prefix: str = "user",
) -> tuple[str, str]:
    """Create a user with a specific role directly (bypasses API).

    Returns (user_id, access_token).
    """
    from core.entities import UserCreate
    from core.entities.user import UserRole
    from core.services.auth_service import _create_access_token

    role = UserRole(role_name)
    user = await user_repo.create(
        UserCreate(
            username=f"{prefix}_{uuid4().hex[:8]}",
            hashed_password="",
            email=f"{prefix}_e2e@test.com",
            name=f"E2E {role_name.title()}",
            role=role,
        ),
    )
    token = _create_access_token(user)
    return str(user.id), token


class TestRBACEndToEnd:
    """Role gates enforced through HTTP on every protected endpoint group."""

    # ── Operator on TRAINER+ endpoints → 403 ─────────────────────────

    async def test_operator_blocked_from_analyst(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Analyst endpoints require TRAINER+ → operator gets 403."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "rbac_op_an", "password": "tmpPw99!!"},
        )
        assert resp.status_code == 201
        hdr = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        resp = await async_client.get("/api/v1/analyst/stats", headers=hdr)
        assert resp.status_code == 403, f"Analyst stats: {resp.text}"

    async def test_operator_blocked_from_curator_quiz(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Curator /quiz requires TRAINER+ → operator gets 403."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "rbac_op_cq", "password": "tmpPw99!!"},
        )
        assert resp.status_code == 201
        hdr = {"Authorization": f"Bearer {resp.json()['access_token']}"}

        resp = await async_client.post(
            "/api/v1/curator/quiz",
            json={"scenario_id": str(uuid4()), "question_count": 3},
            headers=hdr,
        )
        assert resp.status_code == 403

    # ── Admin bypass — 200 on all endpoints ──────────────────────────

    async def test_admin_bypass_analyst(
        self,
        async_client: httpx.AsyncClient,
        user_repo: InMemoryUserRepository,
    ) -> None:
        """Admin bypasses analyst role gate → 200."""
        _, at = await _create_user_with_role(user_repo, "admin")
        hdr = {"Authorization": f"Bearer {at}"}

        resp = await async_client.get("/api/v1/analyst/stats", headers=hdr)
        assert resp.status_code == 200

    async def test_admin_bypass_curator_sync(
        self,
        async_client: httpx.AsyncClient,
        user_repo: InMemoryUserRepository,
    ) -> None:
        """Admin bypasses curator /sync-lms (admin-only) → 200."""
        _, at = await _create_user_with_role(user_repo, "admin")
        hdr = {"Authorization": f"Bearer {at}"}

        resp = await async_client.post(
            "/api/v1/curator/sync-lms",
            json={"plan_id": str(uuid4())},
            headers=hdr,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "synced"

    async def test_admin_bypass_sessions(
        self,
        async_client: httpx.AsyncClient,
        user_repo: InMemoryUserRepository,
    ) -> None:
        """Admin can create sessions (operator+ endpoint)."""
        _, at = await _create_user_with_role(user_repo, "admin")
        hdr = {"Authorization": f"Bearer {at}"}

        resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": str(uuid4())},
            headers=hdr,
        )
        # 404 expected (scenario not found), NOT 403 — gate passed
        assert resp.status_code != 403, "Admin should not get 403"

    async def test_admin_bypass_coach(
        self,
        async_client: httpx.AsyncClient,
        user_repo: InMemoryUserRepository,
    ) -> None:
        """Admin can access coach /simulate endpoint."""
        _, at = await _create_user_with_role(user_repo, "admin")
        hdr = {"Authorization": f"Bearer {at}"}

        resp = await async_client.post(
            "/api/v1/coach/simulate",
            json={"session_id": str(uuid4())},
            headers=hdr,
        )
        # 404 expected (session not found), NOT 403
        assert resp.status_code != 403, "Admin should not get 403"

    # ── Unauthorized → 401 ───────────────────────────────────────────

    async def test_no_auth_on_analyst(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Analyst without auth → 401."""
        resp = await async_client.get("/api/v1/analyst/stats")
        assert resp.status_code == 401

    async def test_no_auth_on_curator_quiz(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Curator /quiz without auth → 401."""
        resp = await async_client.post(
            "/api/v1/curator/quiz",
            json={"scenario_id": str(uuid4()), "question_count": 3},
        )
        assert resp.status_code == 401
