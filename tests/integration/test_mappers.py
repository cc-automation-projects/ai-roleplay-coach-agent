"""Tests for mappers — all entities (no external services required)."""

from datetime import UTC, datetime
from uuid import uuid4

from core.entities.badge import Badge, UserBadge
from core.entities.evaluation import Evaluation
from core.entities.scenario import DifficultyLevel, Psychotype, Scenario
from core.entities.session import Session, SessionStatus
from core.entities.user import User, UserRole
from core.entities.xp import Metric, MetricType, XPReason, XPTransaction
from infrastructure.postgres.mappers.badge_mapper import (
    badge_domain_to_model,
    badge_model_to_domain,
    user_badge_domain_to_model,
    user_badge_model_to_domain,
)
from infrastructure.postgres.mappers.evaluation_mapper import (
    evaluation_domain_to_model,
    evaluation_model_to_domain,
)
from infrastructure.postgres.mappers.scenario_mapper import (
    scenario_domain_to_model,
    scenario_model_to_domain,
)
from infrastructure.postgres.mappers.session_mapper import (
    session_domain_to_model,
    session_model_to_domain,
)
from infrastructure.postgres.mappers.user_mapper import user_domain_to_model, user_model_to_domain
from infrastructure.postgres.mappers.xp_mapper import (
    metric_domain_to_model,
    metric_model_to_domain,
    xp_domain_to_model,
    xp_model_to_domain,
)
from infrastructure.postgres.models.session import SessionModel
from infrastructure.postgres.models.user import UserModel

NOW = datetime.now(UTC)


def _uid() -> str:
    return str(uuid4())


class TestUserMapper:
    def test_model_to_domain_roundtrip(self):
        model = UserModel(
            id=uuid4(),
            tenant_id=uuid4(),
            username="alice",
            email="test@example.com",
            name="Alice",
            hashed_password="",
            role="operator",
            xp_total=500,
            level=1,
            is_active=True,
            created_at=NOW,
            updated_at=NOW,
        )
        domain = user_model_to_domain(model)
        assert domain.email == model.email
        assert domain.role == UserRole.OPERATOR
        assert domain.xp_total == 500

        model2 = user_domain_to_model(domain)
        assert model2.email == model.email
        assert model2.role == "operator"

    def test_domain_to_model_with_none_tenant(self):
        domain = User(
            username="bob",
            hashed_password="",
            email="a@b.com",
            name="Bob",
        )
        model = user_domain_to_model(domain)
        assert model.tenant_id is None


class TestSessionMapper:
    def test_model_to_domain_with_transcript(self):
        model = SessionModel(
            id=uuid4(),
            user_id=uuid4(),
            scenario_id=uuid4(),
            status="in_progress",
            transcript=[
                {
                    "speaker": "operator",
                    "text": "Hello",
                    "timestamp": NOW.isoformat(),
                    "metadata": {},
                },
            ],
            created_at=NOW,
            updated_at=NOW,
        )
        domain = session_model_to_domain(model)
        assert domain.status == SessionStatus.IN_PROGRESS
        assert len(domain.transcript) == 1
        assert domain.transcript[0].speaker == "operator"

        model2 = session_domain_to_model(domain)
        assert model2.status == "in_progress"

    def test_domain_to_model_with_difficulty(self):
        domain = Session(
            user_id=uuid4(),
            scenario_id=uuid4(),
            difficulty_at_start=DifficultyLevel.ADVANCED,
            psychotype_at_start=Psychotype.AGGRESSIVE,
        )
        model = session_domain_to_model(domain)
        assert model.difficulty_at_start == "advanced"
        assert model.psychotype_at_start == "aggressive"


class TestScenarioMapper:
    def test_roundtrip(self):
        domain = Scenario(
            name="Test Scenario",
            description="A test",
            difficulty=DifficultyLevel.EXPERT,
            psychotype=Psychotype.FRAUDSTER,
            script_ref="/scripts/test.md",
            script_text="Hello, I need help with...",
            tags=["fraud", "advanced"],
        )
        model = scenario_domain_to_model(domain)
        assert model.difficulty == "expert"
        assert model.psychotype == "fraudster"
        assert model.tags == ["fraud", "advanced"]

        domain2 = scenario_model_to_domain(model)
        assert domain2.name == domain.name
        assert domain2.difficulty == DifficultyLevel.EXPERT


class TestEvaluationMapper:
    def test_roundtrip(self):
        domain = Evaluation(
            session_id=uuid4(),
            user_id=uuid4(),
            overall_score=85.0,
            script_adherence=80.0,
            tone_score=90.0,
            empathy_score=75.0,
            objection_handling=88.0,
            completeness_score=92.0,
            praise_text="Good job!",
            growth_text="Work on empathy.",
            closing_text="Keep it up!",
            script_citations=["See script section 3.2"],
            gaming_detected=False,
        )
        model = evaluation_domain_to_model(domain)
        assert model.overall_score == 85.0
        assert model.gaming_detected is False

        domain2 = evaluation_model_to_domain(model)
        assert domain2.praise_text == "Good job!"
        assert domain2.grade == "B"


class TestBadgeMapper:
    def test_roundtrip(self):
        domain = Badge(
            name="First Session",
            description="Complete your first session",
            criteria="session_count >= 1",
            xp_reward=100,
        )
        model = badge_domain_to_model(domain)
        assert model.name == "First Session"
        domain2 = badge_model_to_domain(model)
        assert domain2.name == domain.name

    def test_user_badge_roundtrip(self):
        domain = UserBadge(user_id=uuid4(), badge_id=uuid4())
        model = user_badge_domain_to_model(domain)
        domain2 = user_badge_model_to_domain(model)
        assert domain2.user_id == domain.user_id


class TestXPMapper:
    def test_roundtrip(self):
        domain = XPTransaction(
            user_id=uuid4(),
            amount=200,
            reason=XPReason.SESSION_COMPLETED,
            reference_id=uuid4(),
        )
        model = xp_domain_to_model(domain)
        assert model.amount == 200
        assert model.reason == "session_completed"
        domain2 = xp_model_to_domain(model)
        assert domain2.reason == XPReason.SESSION_COMPLETED

    def test_metric_roundtrip(self):
        domain = Metric(
            user_id=uuid4(),
            metric_type=MetricType.AVG_SCORE,
            value=82.5,
        )
        model = metric_domain_to_model(domain)
        assert model.metric_type == "avg_score"
        domain2 = metric_model_to_domain(model)
        assert domain2.metric_type == MetricType.AVG_SCORE
