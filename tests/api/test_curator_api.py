"""API integration tests for /api/v1/curator endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import httpx


class TestCuratorAPI:
    """Curator agent endpoints: learning-plan, quiz, sync-lms."""

    async def test_generate_learning_plan(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /api/v1/curator/learning-plan → 200 with LearningPlan."""
        response = await async_client.post(
            "/api/v1/curator/learning-plan",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "steps" in data
        assert len(data["steps"]) > 0

    async def test_generate_learning_plan_scenario_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """POST with non-existent scenario → 404."""
        response = await async_client.post(
            "/api/v1/curator/learning-plan",
            json={"scenario_id": str(uuid4())},
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_generate_learning_plan_no_auth(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
    ) -> None:
        """POST /learning-plan without auth → 401."""
        response = await async_client.post(
            "/api/v1/curator/learning-plan",
            json={"scenario_id": seeded_scenario["id"]},
        )
        assert response.status_code == 401

    async def test_generate_quiz(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
        rbac_trainer_header: dict[str, str],
    ) -> None:
        """POST /api/v1/curator/quiz → 200 with MicroQuiz."""
        response = await async_client.post(
            "/api/v1/curator/quiz",
            json={
                "scenario_id": seeded_scenario["id"],
                "question_count": 3,
            },
            headers=rbac_trainer_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "quiz" in data
        quiz = data["quiz"]
        assert "questions" in quiz
        assert len(quiz["questions"]) == 3

    async def test_generate_quiz_not_found(
        self,
        async_client: httpx.AsyncClient,
        rbac_trainer_header: dict[str, str],
    ) -> None:
        """POST /quiz with non-existent scenario → 404."""
        response = await async_client.post(
            "/api/v1/curator/quiz",
            json={"scenario_id": str(uuid4()), "question_count": 3},
            headers=rbac_trainer_header,
        )
        assert response.status_code == 404

    async def test_generate_quiz_operator_forbidden(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /quiz as operator → 403 (trainer+ required)."""
        response = await async_client.post(
            "/api/v1/curator/quiz",
            json={"scenario_id": seeded_scenario["id"], "question_count": 3},
            headers=auth_header,
        )
        assert response.status_code == 403

    async def test_sync_lms(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """POST /api/v1/curator/sync-lms → 200 with sync result."""
        response = await async_client.post(
            "/api/v1/curator/sync-lms",
            json={"plan_id": str(uuid4())},
            headers=rbac_admin_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "synced"
        assert "lms_course_id" in data
        assert "lms_url" in data

    async def test_sync_lms_operator_forbidden(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """POST /sync-lms as operator → 403 (admin only)."""
        response = await async_client.post(
            "/api/v1/curator/sync-lms",
            json={"plan_id": str(uuid4())},
            headers=auth_header,
        )
        assert response.status_code == 403
