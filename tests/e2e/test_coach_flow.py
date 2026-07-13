"""E2E: Full coach lifecycle via HTTP.

Tests the complete multi-step flow:
  register → login → create scenario → start session → send turns →
  finish → evaluate → verify stats reflect the session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from core.entities import DifficultyLevel, Psychotype, ScenarioCreate
from core.services.auth_service import _create_access_token

if TYPE_CHECKING:
    import httpx

    from infrastructure.memory.repositories import (
        InMemoryScenarioRepository,
        InMemoryUserRepository,
    )


pytestmark = [pytest.mark.asyncio]


async def _build_trainer_user(
    user_repo: InMemoryUserRepository,
) -> tuple[str, str]:
    """Create a TRAINER user directly and return (user_id, access_token)."""
    from core.entities import UserCreate
    from core.entities.user import UserRole

    user = await user_repo.create(
        UserCreate(
            username=f"trainer_e2e_{uuid4().hex[:8]}",
            hashed_password="",
            email="trainer_e2e@test.com",
            name="E2E Trainer",
            role=UserRole.TRAINER,
        ),
    )
    token = _create_access_token(user)
    return str(user.id), token


class TestFullCoachLifecycle:
    """Complete coach lifecycle spanning auth, sessions, and analyst."""

    async def _register(
        self, client: httpx.AsyncClient, name: str, pw: str = "TestPass123"
    ) -> dict:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"username": name, "password": pw},
        )
        assert resp.status_code == 201, f"Register failed: {resp.text}"
        return resp.json()

    async def _seed_scenario(
        self,
        scenario_repo: InMemoryScenarioRepository,
    ) -> str:
        sc = await scenario_repo.create(
            ScenarioCreate(
                name="E2E Test Scenario",
                description="End-to-end test scenario",
                difficulty=DifficultyLevel.BEGINNER,
                psychotype=Psychotype.NEUTRAL,
                script_ref="E2E-001",
                script_text="Greet. Identify issue. Provide solution. Close.",
                tags=["e2e"],
            ),
        )
        return str(sc.id)

    async def test_full_coach_cycle(
        self,
        async_client: httpx.AsyncClient,
        scenario_repo: InMemoryScenarioRepository,
        user_repo: InMemoryUserRepository,
    ) -> None:
        """Register → login → create session → talk → evaluate → stats.

        Evaluation endpoint requires TRAINER+, so we use a TRAINER user
        for the evaluation step.
        """
        # ── Step 1: Register an operator (who will do the session) ──
        uname = f"coach_e2e_{uuid4().hex[:8]}"
        op = await self._register(async_client, uname)
        op_hdr = {"Authorization": f"Bearer {op['access_token']}"}

        # ── Step 2: Create a TRAINER user for evaluation ──
        _, trainer_at = await _build_trainer_user(user_repo)
        trainer_hdr = {"Authorization": f"Bearer {trainer_at}"}

        # ── Step 3: Seed a scenario ──
        scenario_id = await self._seed_scenario(scenario_repo)

        # ── Step 4: Operator creates session ──
        resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": scenario_id},
            headers=op_hdr,
        )
        assert resp.status_code == 201, f"Session create: {resp.text}"
        session = resp.json()
        session_id = session["id"]
        assert session["status"] == "in_progress"
        # Assumes simulator produces an initial greeting (1st transcript entry).
        # If the simulator greeting logic changes, adjust this assertion.
        assert len(session.get("transcript", [])) >= 1

        # ── Step 5: Operator sends turns ──
        turn1 = await async_client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={
                "user_id": op["user_id"],
                "message": "Hello! I need help with my account.",
            },
            headers=op_hdr,
        )
        assert turn1.status_code == 200, f"Turn 1: {turn1.text}"
        assert len(turn1.json()["transcript"]) >= 2

        turn2 = await async_client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={
                "user_id": op["user_id"],
                "message": "I lost access to my email.",
            },
            headers=op_hdr,
        )
        assert turn2.status_code == 200, f"Turn 2: {turn2.text}"

        # ── Step 6: Operator finishes session ──
        finish = await async_client.post(
            f"/api/v1/sessions/{session_id}/finish",
            headers=op_hdr,
        )
        assert finish.status_code == 200, f"Finish: {finish.text}"
        assert finish.json()["status"] == "completed"

        # ── Step 7: Trainer evaluates ──
        eval_resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/evaluate",
            headers=trainer_hdr,
        )
        assert eval_resp.status_code == 200, f"Evaluate: {eval_resp.text}"
        ev = eval_resp.json()["evaluation"]
        assert ev["overall_score"] > 0

        # ── Step 8: Verify analyst stats reflect the session ──
        stats = await async_client.get(
            f"/api/v1/analyst/stats/{op['user_id']}",
            headers=trainer_hdr,
        )
        assert stats.status_code == 200
        data = stats.json()
        assert data["total_sessions"] >= 1
        assert data["avg_overall_score"] == pytest.approx(ev["overall_score"])

    async def test_scenario_not_found_returns_404(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """Creating a session with a non-existent scenario → 404."""
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "scenario_404", "password": "TestPass123"},
        )
        assert resp.status_code == 201
        at = resp.json()["access_token"]

        fake_id = str(uuid4())
        resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": fake_id},
            headers={"Authorization": f"Bearer {at}"},
        )
        assert resp.status_code == 404
