"""Tests for SessionService — session lifecycle orchestration."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from core.entities import (
    DifficultyLevel,
    Evaluation,
    Psychotype,
    Scenario,
    Session,
    SessionStatus,
    TranscriptEntry,
)
from core.exceptions import BusinessRuleViolationError, NotFoundError
from core.services.session_service import SessionService


class TestSessionService:
    """SessionService: start → process_turn → finish orchestration."""

    @pytest.fixture
    def mock_repos(self):
        """Return a plain object with async mock attributes."""
        from types import SimpleNamespace

        return SimpleNamespace(
            session_repo=AsyncMock(),
            scenario_repo=AsyncMock(),
        )

    @pytest.fixture
    def mock_agents(self):
        return AsyncMock(simulator=AsyncMock(), coach=AsyncMock())

    @pytest.fixture
    def service(self, mock_repos, mock_agents):
        return SessionService(
            session_repo=mock_repos.session_repo,
            scenario_repo=mock_repos.scenario_repo,
            simulator=mock_agents.simulator,
            coach=mock_agents.coach,
        )

    # ── start_session ──────────────────────────────────────────────────

    async def test_start_session_success(self, mock_repos, mock_agents, service):
        """Happy path: start a new session with simulator greeting."""
        user_id = uuid4()
        scenario_id = uuid4()
        scenario = Scenario(
            id=scenario_id,
            name="Angry customer",
            description="Aggressive client test",
            script_ref="s-001",
            script_text="Full script text here...",
            psychotype=Psychotype.AGGRESSIVE,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )
        mock_repos.scenario_repo.get_by_id.return_value = scenario
        mock_agents.simulator.start_dialogue.return_value = (
            "Hello, I have a complaint!",
            Psychotype.AGGRESSIVE,
        )

        mock_repos.session_repo.create.return_value = Session(
            id=uuid4(),
            user_id=user_id,
            scenario_id=scenario_id,
            status=SessionStatus.IN_PROGRESS,
            difficulty_at_start=DifficultyLevel.INTERMEDIATE,
            psychotype_at_start=Psychotype.AGGRESSIVE,
            transcript=[TranscriptEntry(speaker="client", text="Hello")],
        )

        result = await service.start_session(
            user_id=user_id, scenario_id=scenario_id
        )

        assert result.status == SessionStatus.IN_PROGRESS
        assert result.difficulty_at_start == DifficultyLevel.INTERMEDIATE
        assert result.psychotype_at_start == Psychotype.AGGRESSIVE
        assert result.transcript[0].speaker == "client"
        mock_repos.scenario_repo.get_by_id.assert_awaited_once_with(scenario_id)
        mock_agents.simulator.start_dialogue.assert_awaited_once_with(scenario)
        mock_repos.session_repo.create.assert_awaited_once()

    async def test_start_session_scenario_not_found(self, mock_repos, service):
        """Raise NotFoundError when scenario does not exist."""
        mock_repos.scenario_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Scenario"):
            await service.start_session(user_id=uuid4(), scenario_id=uuid4())

    # ── process_turn ───────────────────────────────────────────────────

    async def test_process_turn_happy_path(self, mock_repos, mock_agents, service):
        """Operator sends text → client responds via simulator."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            user_id=uuid4(),
            scenario_id=uuid4(),
            status=SessionStatus.IN_PROGRESS,
        )
        mock_repos.session_repo.get_by_id.return_value = session

        async def _update(s):
            return s

        mock_repos.session_repo.update.side_effect = _update
        mock_agents.simulator.generate_response.return_value = (
            "I am not satisfied with your answer!"
        )

        entry = await service.process_turn(
            session_id=session_id, operator_text="I understand your concern."
        )

        assert entry.speaker == "client"
        assert entry.text == "I am not satisfied with your answer!"
        mock_repos.session_repo.get_by_id.assert_awaited_once_with(session_id)
        mock_agents.simulator.generate_response.assert_awaited_once()
        mock_repos.session_repo.update.assert_awaited_once()

    async def test_process_turn_session_not_found(self, mock_repos, service):
        """Raise NotFoundError when session does not exist."""
        mock_repos.session_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Session"):
            await service.process_turn(session_id=uuid4(), operator_text="Hi")

    async def test_process_turn_session_not_in_progress(self, mock_repos, service):
        """Raise BusinessRuleViolationError when session is completed."""
        mock_repos.session_repo.get_by_id.return_value = Session(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=uuid4(),
            status=SessionStatus.COMPLETED,
        )

        with pytest.raises(BusinessRuleViolationError, match="not in progress"):
            await service.process_turn(session_id=uuid4(), operator_text="Hi")

    # ── finish_session ─────────────────────────────────────────────────

    async def test_finish_session_happy_path(self, mock_repos, service):
        """Complete a session — marks as COMPLETED."""
        session_id = uuid4()
        session = Session(
            id=session_id,
            user_id=uuid4(),
            scenario_id=uuid4(),
            status=SessionStatus.IN_PROGRESS,
        )
        mock_repos.session_repo.get_by_id.return_value = session

        async def _update(s):
            return s

        mock_repos.session_repo.update.side_effect = _update

        result = await service.finish_session(session_id=session_id)

        assert result.status == SessionStatus.COMPLETED
        mock_repos.session_repo.get_by_id.assert_awaited_once_with(session_id)
        mock_repos.session_repo.update.assert_awaited_once()

    async def test_finish_session_not_found(self, mock_repos, service):
        """Raise NotFoundError when session does not exist."""
        mock_repos.session_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Session"):
            await service.finish_session(session_id=uuid4())

    # ── evaluate_session ───────────────────────────────────────────────

    async def test_evaluate_session_happy_path(
        self, mock_repos, mock_agents, service
    ):
        """Evaluate a completed session via Coach agent."""
        session_id = uuid4()
        scenario_id = uuid4()
        user_id = uuid4()
        session = Session(
            id=session_id,
            user_id=user_id,
            scenario_id=scenario_id,
            status=SessionStatus.COMPLETED,
        )
        scenario = Scenario(
            id=scenario_id,
            name="Test",
            description="Test scenario",
            script_ref="s-001",
            script_text="Script text here...",
        )
        evaluation = Evaluation(
            session_id=session_id,
            user_id=user_id,
            overall_score=85.0,
            script_adherence=80.0,
            tone_score=85.0,
            empathy_score=75.0,
            objection_handling=80.0,
            completeness_score=90.0,
        )
        mock_repos.session_repo.get_by_id.return_value = session
        mock_repos.scenario_repo.get_by_id.return_value = scenario
        mock_agents.coach.evaluate_session.return_value = evaluation

        result = await service.evaluate_session(session_id=session_id)

        assert result.overall_score == 85.0
        assert result.session_id == session_id
        mock_repos.session_repo.get_by_id.assert_awaited_once_with(session_id)
        mock_repos.scenario_repo.get_by_id.assert_awaited_once_with(scenario_id)
        mock_agents.coach.evaluate_session.assert_awaited_once_with(session, scenario)

    async def test_evaluate_session_not_found(self, mock_repos, service):
        """Raise NotFoundError when session does not exist."""
        mock_repos.session_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Session"):
            await service.evaluate_session(session_id=uuid4())

    # ── get_session ────────────────────────────────────────────────────

    async def test_get_session(self, mock_repos, service):
        """Retrieve a session by ID."""
        session_id = uuid4()
        session = Session(
            id=session_id, user_id=uuid4(), scenario_id=uuid4()
        )
        mock_repos.session_repo.get_by_id.return_value = session

        result = await service.get_session(session_id=session_id)

        assert result.id == session_id
        mock_repos.session_repo.get_by_id.assert_awaited_once_with(session_id)

    async def test_get_session_not_found(self, mock_repos, service):
        """Raise NotFoundError when session does not exist."""
        mock_repos.session_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Session"):
            await service.get_session(session_id=uuid4())
