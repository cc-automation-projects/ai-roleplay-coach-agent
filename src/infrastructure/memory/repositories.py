"""In-memory implementations of all repository protocols."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from core.entities import (
    Badge,
    BadgeCreate,
    Evaluation,
    EvaluationCreate,
    Scenario,
    ScenarioCreate,
    Session,
    SessionCreate,
    SessionStatus,
    User,
    UserBadge,
    UserCreate,
    XPTransaction,
)
from core.exceptions import DuplicateError, NotFoundError

if TYPE_CHECKING:
    from uuid import UUID


class BaseInMemoryRepository[T]:
    """Generic CRUD — get_by_id, list_all, update, delete, count."""

    _entity_name: str = "Entity"

    def __init__(self) -> None:
        self._items: dict[UUID, T] = {}

    async def get_by_id(self, item_id: UUID) -> T | None:
        return self._items.get(item_id)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        return list(self._items.values())[skip : skip + limit]

    async def update(self, item: T) -> T:
        item_id = item.id  # type: ignore[attr-defined]
        if item_id not in self._items:
            raise NotFoundError(self._entity_name, str(item_id))
        self._items[item_id] = item
        return item

    async def delete(self, item_id: UUID) -> None:
        if item_id not in self._items:
            raise NotFoundError(self._entity_name, str(item_id))
        del self._items[item_id]

    async def count(self) -> int:
        return len(self._items)


class InMemoryUserRepository(BaseInMemoryRepository[User]):
    """User storage with email/username indexes."""

    _entity_name = "User"

    def __init__(self) -> None:
        super().__init__()
        self._by_email: dict[str, User] = {}
        self._by_username: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email.lower())

    async def get_by_username(self, username: str) -> User | None:
        return self._by_username.get(username.lower())

    async def create(self, data: UserCreate) -> User:
        if data.email.lower() in self._by_email:
            msg = f"User with email {data.email} already exists"
            raise DuplicateError(msg)
        if data.username.lower() in self._by_username:
            msg = f"User with username {data.username} already exists"
            raise DuplicateError(msg)
        user = User(
            username=data.username, hashed_password=data.hashed_password,
            email=data.email, name=data.name, role=data.role,
        )
        self._items[user.id] = user
        self._by_email[data.email.lower()] = user
        self._by_username[data.username.lower()] = user
        return user

    async def update(self, user: User) -> User:
        old = self._items.get(user.id)
        if old is None:
            raise NotFoundError(self._entity_name, str(user.id))
        self._items[user.id] = user
        if old.email.lower() != user.email.lower():
            self._by_email.pop(old.email.lower(), None)
            self._by_email[user.email.lower()] = user
        return user

    async def delete(self, user_id: UUID) -> None:
        user = self._items.pop(user_id, None)
        if user is None:
            raise NotFoundError(self._entity_name, str(user_id))
        self._by_email.pop(user.email.lower(), None)
        self._by_username.pop(user.username.lower(), None)

    async def get_leaderboard(self, limit: int = 10, skip: int = 0) -> list[User]:
        sorted_users = sorted(
            self._items.values(),
            key=lambda u: (-u.xp_total, u.name or str(u.id)),
        )
        return sorted_users[skip : skip + limit]

    async def get_users_by_attributes(
        self, attributes: dict[str, str]
    ) -> list[User]:
        return [
            user for user in self._items.values()
            if all(
                getattr(user, attr, None) == val
                for attr, val in attributes.items()
            )
        ]


class InMemorySessionRepository(BaseInMemoryRepository[Session]):
    """Session storage."""

    _entity_name = "Session"

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Session]:
        all_for_user = [s for s in self._items.values() if s.user_id == user_id]
        return all_for_user[skip : skip + limit]

    async def create(self, data: SessionCreate) -> Session:
        session = Session(
            user_id=data.user_id, scenario_id=data.scenario_id,
            status=data.status, transcript=list(data.transcript),
            difficulty_at_start=data.difficulty_at_start,
            psychotype_at_start=data.psychotype_at_start,
        )
        self._items[session.id] = session
        return session

    async def count_by_user(self, user_id: UUID) -> int:
        return sum(1 for s in self._items.values() if s.user_id == user_id)

    async def count_completed(self, user_id: UUID) -> int:
        return sum(
            1 for s in self._items.values()
            if s.user_id == user_id and s.status == SessionStatus.COMPLETED
        )


class InMemoryScenarioRepository(BaseInMemoryRepository[Scenario]):
    """Scenario storage with seed data."""

    _entity_name = "Scenario"

    def seed(self, scenario: Scenario) -> None:
        self._items[scenario.id] = scenario

    async def create(self, data: ScenarioCreate) -> Scenario:
        scenario = Scenario(
            name=data.name, description=data.description,
            difficulty=data.difficulty, psychotype=data.psychotype,
            script_ref=data.script_ref, script_text=data.script_text,
            tags=data.tags,
        )
        self._items[scenario.id] = scenario
        return scenario

    async def list_by_difficulty(
        self, difficulty: str, skip: int = 0, limit: int = 100
    ) -> list[Scenario]:
        return [
            s for s in self._items.values()
            if s.difficulty.value == difficulty
        ][skip : skip + limit]

    async def count_by_difficulty(self, difficulty: str) -> int:
        return sum(1 for s in self._items.values() if s.difficulty.value == difficulty)


class InMemoryEvaluationRepository(BaseInMemoryRepository[Evaluation]):
    """Evaluation storage."""

    _entity_name = "Evaluation"

    def __init__(self) -> None:
        super().__init__()
        # Optional cross-reference for scenario-based filtering
        self._sessions_by_id: dict[UUID, Session] = {}

    async def get_by_session(self, session_id: UUID) -> Evaluation | None:
        for ev in self._items.values():
            if ev.session_id == session_id:
                return copy.deepcopy(ev)
        return None

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Evaluation]:
        return [
            ev for ev in self._items.values() if ev.user_id == user_id
        ][skip : skip + limit]

    async def create(self, data: EvaluationCreate) -> Evaluation:
        evaluation = Evaluation(
            session_id=data.session_id, user_id=data.user_id,
            overall_score=data.overall_score,
            script_adherence=data.script_adherence, tone_score=data.tone_score,
            empathy_score=data.empathy_score,
            objection_handling=data.objection_handling,
            completeness_score=data.completeness_score,
        )
        self._items[evaluation.id] = evaluation
        return evaluation

    async def get_average_score(self, user_id: UUID) -> float:
        scores = [ev.overall_score for ev in self._items.values() if ev.user_id == user_id]
        return sum(scores) / len(scores) if scores else 0.0

    async def get_scores_by_user_ids(
        self,
        user_ids: list[UUID],
        scenario_ids: list[UUID] | None = None,
    ) -> dict[UUID, list[float]]:
        result: dict[UUID, list[float]] = {}
        for ev in self._items.values():
            if ev.user_id not in user_ids:
                continue
            if scenario_ids:
                session = self._sessions_by_id.get(ev.session_id)
                if session is None or session.scenario_id not in scenario_ids:
                    continue
            result.setdefault(ev.user_id, []).append(ev.overall_score)
        return result


class InMemoryBadgeRepository(BaseInMemoryRepository[Badge]):
    """Badge storage."""

    _entity_name = "Badge"

    def __init__(self) -> None:
        super().__init__()
        self._user_badges: dict[UUID, list[UserBadge]] = {}

    async def create(self, data: BadgeCreate) -> Badge:
        badge = Badge(
            name=data.name, description=data.description, criteria=data.criteria,
            icon_url=data.icon_url, xp_reward=data.xp_reward, is_hidden=data.is_hidden,
        )
        self._items[badge.id] = badge
        return badge

    async def award_to_user(self, user_badge: UserBadge) -> UserBadge:
        self._user_badges.setdefault(user_badge.user_id, []).append(user_badge)
        return user_badge

    async def get_user_badges(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Badge]:
        badge_ids = [ub.badge_id for ub in self._user_badges.get(user_id, [])]
        return [b for b_id, b in self._items.items() if b_id in badge_ids][skip : skip + limit]

    async def count_user_badges(self, user_id: UUID) -> int:
        return len(self._user_badges.get(user_id, []))

    async def has_user_badge(self, user_id: UUID, badge_id: UUID) -> bool:
        return any(ub.badge_id == badge_id for ub in self._user_badges.get(user_id, []))


class InMemoryXPTransactionRepository:
    """XP transaction storage (list-based, no standard CRUD)."""

    def __init__(self) -> None:
        self._txns: list[XPTransaction] = []

    async def create(self, txn: XPTransaction) -> XPTransaction:
        self._txns.append(txn)
        return txn

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[XPTransaction]:
        return [t for t in self._txns if t.user_id == user_id][skip : skip + limit]

    async def count_by_user(self, user_id: UUID) -> int:
        return sum(1 for t in self._txns if t.user_id == user_id)

    async def get_total_xp(self, user_id: UUID) -> int:
        return sum(t.amount for t in self._txns if t.user_id == user_id)
