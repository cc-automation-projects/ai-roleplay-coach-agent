"""Smoke tests for core domain entities."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from core.entities import (
    Badge,
    BadgeCreate,
    DifficultyLevel,
    Evaluation,
    Metric,
    MetricType,
    Psychotype,
    Scenario,
    Session,
    SessionStatus,
    SessionUpdate,
    TranscriptEntry,
    User,
    UserCreate,
    UserRole,
    UserUpdate,
    XPReason,
    XPTransaction,
)


class TestUserEntity:
    """User entity creation and behavior."""

    def test_create_user(self) -> None:
        user = User(
            username="operator",
            hashed_password="",
            email="t@t.com",
            name="Test Operator",
        )
        assert user.email == "t@t.com"
        assert user.name == "Test Operator"
        assert user.role == UserRole.OPERATOR
        assert user.xp_total == 0
        assert user.level == 1
        assert isinstance(user.id, UUID)
        assert user.is_active is True

    def test_user_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            User(
                username="bad",
                hashed_password="",
                email="bad-email",
                name="Bad Email",
            )

    def test_user_add_xp(self) -> None:
        user = User(
            username="test",
            hashed_password="",
            email="t@t.com",
            name="Test",
        )
        user.add_xp(500)
        assert user.xp_total == 500
        assert user.level == 1
        user.add_xp(500)
        assert user.xp_total == 1000
        assert user.level == 2

    def test_user_negative_xp(self) -> None:
        user = User(
            username="test",
            hashed_password="",
            email="t@t.com",
            name="Test",
        )
        with pytest.raises(ValueError, match="non-negative"):
            user.add_xp(-100)

    def test_user_create_dto(self) -> None:
        dto = UserCreate(
            username="new",
            hashed_password="",
            email="new@t.com",
            name="New",
        )
        assert dto.email == "new@t.com"
        assert dto.role == UserRole.OPERATOR

    def test_user_update_dto(self) -> None:
        dto = UserUpdate(name="Updated", is_active=False)
        assert dto.name == "Updated"
        assert dto.is_active is False
        assert dto.role is None


class TestSessionEntity:
    """Session entity tests."""

    def test_create_session(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        session = Session(user_id=uid, scenario_id=sid)
        assert session.status == SessionStatus.PENDING
        assert session.transcript == []
        assert isinstance(session.id, UUID)

    def test_transcript_entry(self) -> None:
        entry = TranscriptEntry(speaker="operator", text="Hello")
        assert entry.speaker == "operator"
        assert isinstance(entry.timestamp, datetime)

    def test_session_with_transcript(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        entries = [
            TranscriptEntry(speaker="operator", text="Hello"),
            TranscriptEntry(speaker="client", text="I have a problem"),
        ]
        session = Session(user_id=uid, scenario_id=sid, transcript=entries)
        assert len(session.transcript) == 2
        assert session.transcript[0].speaker == "operator"

    def test_session_update_dto(self) -> None:
        dto = SessionUpdate(status=SessionStatus.IN_PROGRESS)
        assert dto.status == SessionStatus.IN_PROGRESS
        assert dto.started_at is None

    def test_transcript_max_100_entries(self) -> None:
        """L7: Transcript limited to max 100 entries via field_validator."""
        uid = UUID(int=1)
        sid = UUID(int=2)
        entries = [
            TranscriptEntry(speaker="operator", text=f"Entry {i}")
            for i in range(120)
        ]
        session = Session(user_id=uid, scenario_id=sid, transcript=entries)
        assert len(session.transcript) == 100  # only last 100 kept

    def test_transcript_append_respects_limit(self) -> None:
        """L7: append_transcript_entry also respects 100-entry limit."""
        uid = UUID(int=1)
        sid = UUID(int=2)
        entries = [
            TranscriptEntry(speaker="operator", text=f"Entry {i}")
            for i in range(100)
        ]
        session = Session(user_id=uid, scenario_id=sid, transcript=entries)
        session.append_transcript_entry(speaker="client", text="Overflow")
        # len stays 100 but last entry is the new one
        assert len(session.transcript) == 100
        assert session.transcript[-1].text == "Overflow"
        assert session.transcript[-1].speaker == "client"


class TestScenarioEntity:
    """Scenario entity tests."""

    def test_create_scenario(self) -> None:
        scenario = Scenario(
            name="Angry customer",
            description="Aggressive client",
            script_ref="s-001",
            script_text="Full script text here...",
            psychotype=Psychotype.AGGRESSIVE,
            difficulty=DifficultyLevel.ADVANCED,
        )
        assert scenario.name == "Angry customer"
        assert scenario.psychotype == Psychotype.AGGRESSIVE
        assert scenario.is_active is True

    def test_scenario_defaults(self) -> None:
        scenario = Scenario(
            name="Simple",
            description="A neutral client",
            script_ref="s-002",
            script_text="text",
        )
        assert scenario.difficulty == DifficultyLevel.BEGINNER
        assert scenario.psychotype == Psychotype.NEUTRAL


class TestEvaluationEntity:
    """Evaluation entity tests."""

    def test_create_evaluation(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        ev = Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=85.0,
            script_adherence=90.0,
            tone_score=80.0,
            empathy_score=75.0,
            objection_handling=85.0,
            completeness_score=90.0,
        )
        assert ev.overall_score == 85.0
        assert ev.is_passing is True
        assert ev.grade == "B"

    def test_evaluation_failing(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        ev = Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=55.0,
            script_adherence=50.0,
            tone_score=60.0,
            empathy_score=40.0,
            objection_handling=50.0,
            completeness_score=60.0,
        )
        assert ev.is_passing is False
        assert ev.grade == "F"

    def test_evaluation_grade_a(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        ev = Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=95.0,
            script_adherence=90.0,
            tone_score=90.0,
            empathy_score=90.0,
            objection_handling=90.0,
            completeness_score=90.0,
        )
        assert ev.grade == "A"
        assert ev.is_passing is True

    def test_evaluation_grade_c(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        ev = Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=75.0,
            script_adherence=70.0,
            tone_score=70.0,
            empathy_score=70.0,
            objection_handling=70.0,
            completeness_score=70.0,
        )
        assert ev.grade == "C"
        assert ev.is_passing is True

    def test_evaluation_grade_d(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        ev = Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=65.0,
            script_adherence=60.0,
            tone_score=60.0,
            empathy_score=60.0,
            objection_handling=60.0,
            completeness_score=60.0,
        )
        assert ev.grade == "D"
        assert ev.is_passing is False

    def test_evaluation_invalid_score(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        with pytest.raises(ValidationError):
            Evaluation(
                session_id=sid,
                user_id=uid,
                overall_score=150.0,
                script_adherence=50.0,
                tone_score=50.0,
                empathy_score=50.0,
                objection_handling=50.0,
                completeness_score=50.0,
            )


class TestBadgeEntity:
    """Badge entity tests."""

    def test_create_badge(self) -> None:
        badge = Badge(
            name="Anger Tamer",
            description="Complete 3 aggressive scenarios with A grade",
            criteria="complete_aggressive >= 3 AND avg_score >= 90",
            xp_reward=500,
        )
        assert badge.name == "Anger Tamer"
        assert badge.xp_reward == 500
        assert badge.is_hidden is False

    def test_create_badge_dto(self) -> None:
        dto = BadgeCreate(
            name="New Badge",
            description="Test description",
            criteria="test >= 1",
            xp_reward=200,
            is_hidden=True,
        )
        assert dto.name == "New Badge"
        assert dto.is_hidden is True


class TestXPEntity:
    """XP transaction tests."""

    def test_create_xp_transaction(self) -> None:
        txn = XPTransaction(
            user_id=UUID(int=1),
            amount=100,
            reason=XPReason.SESSION_COMPLETED,
        )
        assert txn.amount == 100
        assert txn.reason == XPReason.SESSION_COMPLETED

    def test_xp_penalty(self) -> None:
        txn = XPTransaction(
            user_id=UUID(int=1),
            amount=-50,
            reason=XPReason.SESSION_COMPLETED,
        )
        assert txn.amount < 0


class TestDTOSerialization:
    """DTO roundtrip serialization tests (TE6)."""

    def test_user_create_roundtrip(self) -> None:
        dto = UserCreate(
            username="op1",
            hashed_password="",
            email="op@test.com",
            name="Operator One",
        )
        dumped = dto.model_dump()
        restored = UserCreate.model_validate(dumped)
        assert restored.email == dto.email
        assert restored.name == dto.name
        assert restored.role == UserRole.OPERATOR

    def test_session_update_roundtrip(self) -> None:
        dto = SessionUpdate(status=SessionStatus.IN_PROGRESS)
        dumped = dto.model_dump()
        restored = SessionUpdate.model_validate(dumped)
        assert restored.status == SessionStatus.IN_PROGRESS
        assert restored.started_at is None

    def test_session_roundtrip(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        session = Session(user_id=uid, scenario_id=sid)
        dumped = session.model_dump(mode="json")
        restored = Session.model_validate(dumped)
        assert restored.user_id == uid
        assert restored.scenario_id == sid
        assert restored.status == SessionStatus.PENDING
        assert restored.transcript == []

    def test_session_with_transcript_roundtrip(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        entries = [
            TranscriptEntry(speaker="operator", text="Hello"),
            TranscriptEntry(speaker="client", text="Hi there"),
        ]
        session = Session(user_id=uid, scenario_id=sid, transcript=entries)
        dumped = session.model_dump(mode="json")
        restored = Session.model_validate(dumped)
        assert len(restored.transcript) == 2
        assert restored.transcript[0].speaker == "operator"
        assert restored.transcript[1].text == "Hi there"

    def test_scenario_roundtrip(self) -> None:
        scenario = Scenario(
            name="Angry customer",
            description="Aggressive client",
            script_ref="s-001",
            script_text="Full script text here...",
        )
        dumped = scenario.model_dump(mode="json")
        restored = Scenario.model_validate(dumped)
        assert restored.name == "Angry customer"
        assert restored.is_active is True

    def test_evaluation_roundtrip(self) -> None:
        uid = UUID(int=1)
        sid = UUID(int=2)
        ev = Evaluation(
            session_id=sid,
            user_id=uid,
            overall_score=85.0,
            script_adherence=90.0,
            tone_score=80.0,
            empathy_score=75.0,
            objection_handling=85.0,
            completeness_score=90.0,
        )
        dumped = ev.model_dump(mode="json")
        restored = Evaluation.model_validate(dumped)
        assert restored.overall_score == 85.0
        assert restored.grade == "B"
        assert restored.is_passing is True

    def test_badge_create_roundtrip(self) -> None:
        dto = BadgeCreate(
            name="Test Badge",
            description="A test badge",
            criteria="test >= 1",
            xp_reward=200,
            is_hidden=True,
        )
        dumped = dto.model_dump()
        restored = BadgeCreate.model_validate(dumped)
        assert restored.name == "Test Badge"
        assert restored.xp_reward == 200
        assert restored.is_hidden is True

    def test_xp_transaction_roundtrip(self) -> None:
        txn = XPTransaction(
            user_id=UUID(int=1),
            amount=100,
            reason=XPReason.SESSION_COMPLETED,
        )
        dumped = txn.model_dump(mode="json")
        restored = XPTransaction.model_validate(dumped)
        assert restored.amount == 100
        assert restored.reason == XPReason.SESSION_COMPLETED

    def test_user_update_roundtrip_partial(self) -> None:
        """Partial update: only one field set."""
        dto = UserUpdate(name="Updated Name")
        dumped = dto.model_dump(exclude_none=True)
        assert "name" in dumped
        assert "role" not in dumped  # only name was set
        restored = UserUpdate.model_validate(dumped)
        assert restored.name == "Updated Name"
        assert restored.role is None


class TestMetricEntity:
    """Analytics metric tests."""

    def test_create_metric(self) -> None:
        metric = Metric(
            user_id=UUID(int=1),
            metric_type=MetricType.AVG_SCORE,
            value=85.5,
        )
        assert metric.metric_type == MetricType.AVG_SCORE
        assert metric.value == 85.5
