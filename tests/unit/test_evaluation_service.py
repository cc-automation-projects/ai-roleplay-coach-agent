"""Tests for EvaluationService — saving and querying evaluations."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from core.entities import Evaluation, User
from core.services.evaluation_service import EvaluationService


class _MockRepos:
    """Namespace for mock repos — avoids AsyncMock dict iteration issue."""

    def __init__(self) -> None:
        self.eval_repo = AsyncMock()
        self.user_repo = AsyncMock()
        self.xp_repo = AsyncMock()


class TestEvaluationService:
    """EvaluationService: save, average, trend."""

    @pytest.fixture
    def mock_repos(self):
        return _MockRepos()

    @pytest.fixture
    def service(self, mock_repos):
        return EvaluationService(
            eval_repo=mock_repos.eval_repo,
            user_repo=mock_repos.user_repo,
            xp_repo=mock_repos.xp_repo,
        )

    # ── save_evaluation ────────────────────────────────────────────────

    async def test_save_evaluation_passing(self, mock_repos, service):
        """Save a passing evaluation and award XP."""
        user_id = uuid4()
        evaluation = Evaluation(
            session_id=uuid4(),
            user_id=user_id,
            overall_score=85.0,
            script_adherence=80.0,
            tone_score=85.0,
            empathy_score=75.0,
            objection_handling=80.0,
            completeness_score=90.0,
        )
        mock_repos.eval_repo.create.return_value = evaluation
        real_user = User(
            id=user_id,
            username="test",
            hashed_password="",
            email="t@t.com",
            name="Test",
        )
        mock_repos.user_repo.get_by_id.return_value = real_user

        result = await service.save_evaluation(evaluation)

        assert result.overall_score == 85.0
        mock_repos.eval_repo.create.assert_awaited_once_with(evaluation)
        mock_repos.user_repo.get_by_id.assert_awaited_once_with(user_id)
        mock_repos.xp_repo.create.assert_awaited_once()  # passing → XP awarded

    async def test_save_evaluation_failing(self, mock_repos, service):
        """Save a failing evaluation without XP award."""
        evaluation = Evaluation(
            session_id=uuid4(),
            user_id=uuid4(),
            overall_score=45.0,
            script_adherence=40.0,
            tone_score=50.0,
            empathy_score=35.0,
            objection_handling=40.0,
            completeness_score=50.0,
        )
        mock_repos.eval_repo.create.return_value = evaluation

        result = await service.save_evaluation(evaluation)

        assert result.overall_score == 45.0
        mock_repos.eval_repo.create.assert_awaited_once()
        # For failing scores, no XP is awarded
        mock_repos.xp_repo.create.assert_not_called()

    # ── get_user_average ───────────────────────────────────────────────

    async def test_get_user_average(self, mock_repos, service):
        """Return average score from repository."""
        mock_repos.eval_repo.get_average_score.return_value = 75.5

        score = await service.get_user_average(user_id=uuid4())

        assert score == 75.5
        mock_repos.eval_repo.get_average_score.assert_awaited_once()

    # ── get_user_trend ─────────────────────────────────────────────────

    async def test_get_user_trend(self, mock_repos, service):
        """Return recent evaluations as trend data."""
        user_id = uuid4()
        evaluations = [
            Evaluation(
                session_id=uuid4(),
                user_id=user_id,
                overall_score=float(70 + i * 5),
                script_adherence=75.0,
                tone_score=75.0,
                empathy_score=70.0,
                objection_handling=75.0,
                completeness_score=80.0,
            )
            for i in range(5)
        ]
        mock_repos.eval_repo.list_by_user.return_value = evaluations

        trend = await service.get_user_trend(user_id=user_id, last_n=5)

        assert len(trend) == 5
        assert trend[0]["score"] == 70.0
        assert trend[-1]["score"] == 90.0
        assert "grade" in trend[0]
        assert "session_id" in trend[0]
        mock_repos.eval_repo.list_by_user.assert_awaited_once_with(
            user_id, skip=0, limit=5
        )

    async def test_get_user_trend_empty(self, mock_repos, service):
        """Return empty list when user has no evaluations."""
        mock_repos.eval_repo.list_by_user.return_value = []

        trend = await service.get_user_trend(user_id=uuid4(), last_n=10)

        assert trend == []
        mock_repos.eval_repo.list_by_user.assert_awaited_once()

    # ── get_user_grade_summary ─────────────────────────────────────────

    async def test_get_user_grade_summary(self, mock_repos, service):
        """Summarise grade distribution for a user."""
        user_id = uuid4()
        evaluations = [
            Evaluation(
                session_id=uuid4(), user_id=user_id,
                overall_score=95.0, script_adherence=90.0, tone_score=90.0,
                empathy_score=90.0, objection_handling=90.0, completeness_score=90.0,
            ),
            Evaluation(
                session_id=uuid4(), user_id=user_id,
                overall_score=75.0, script_adherence=70.0, tone_score=70.0,
                empathy_score=70.0, objection_handling=70.0, completeness_score=70.0,
            ),
            Evaluation(
                session_id=uuid4(), user_id=user_id,
                overall_score=55.0, script_adherence=50.0, tone_score=50.0,
                empathy_score=50.0, objection_handling=50.0, completeness_score=50.0,
            ),
        ]
        mock_repos.eval_repo.list_by_user.return_value = evaluations

        summary = await service.get_user_grade_summary(user_id=user_id)

        assert summary["A"] == 1
        assert summary["C"] == 1
        assert summary["F"] == 1
        assert summary["total"] == 3
        assert summary["average"] == 75.0
