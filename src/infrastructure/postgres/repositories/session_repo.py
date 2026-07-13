"""PostgreSQL implementation of SessionRepository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.session import Session, SessionCreate
from core.exceptions import NotFoundError
from infrastructure.postgres.mappers.session_mapper import (
    session_domain_to_model,
    session_model_to_domain,
)
from infrastructure.postgres.models.session import SessionModel
from infrastructure.postgres.repositories.base import BaseRepo


class SessionRepo(BaseRepo[SessionModel]):
    """PostgreSQL implementation of SessionRepository protocol."""

    model_cls = SessionModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, session_id: UUID) -> Session | None:
        model = await self._get_by_id(self._session, session_id)
        return session_model_to_domain(model) if model else None

    async def list_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> list[Session]:
        stmt = (
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .order_by(SessionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._safe_call("list_by_user", self._session.execute(stmt))
        models = list(result.scalars().all())
        return [session_model_to_domain(m) for m in models]

    async def create(self, data: SessionCreate) -> Session:
        domain = Session(
            user_id=data.user_id,
            scenario_id=data.scenario_id,
        )
        model = session_domain_to_model(domain)
        self._session.add(model)
        await self._session.flush()
        return session_model_to_domain(model)

    async def update(self, session: Session) -> Session:
        existing = await self._get_by_id(self._session, session.id)
        if existing is None:
            msg = "Session"
            raise NotFoundError(msg, str(session.id))
        model = session_domain_to_model(session)
        await self._session.merge(model)
        await self._session.flush()
        return session

    async def delete(self, session_id: UUID) -> None:
        await self._delete(self._session, session_id)

    async def count_by_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(SessionModel).where(SessionModel.user_id == user_id)
        result = await self._safe_call("count_by_user", self._session.execute(stmt))
        return result.scalar_one()

    async def count_completed(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(SessionModel)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.status == "completed")
        )
        result = await self._safe_call("count_completed", self._session.execute(stmt))
        return result.scalar_one()
