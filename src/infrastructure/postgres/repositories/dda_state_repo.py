"""PostgreSQL implementation of DDAStateRepository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.dda_state import DDAState, DDAStateCreate
from infrastructure.postgres.mappers.dda_state_mapper import (
    dda_state_domain_to_model,
    dda_state_model_to_domain,
)
from infrastructure.postgres.models.dda_state import DDAStateModel
from infrastructure.postgres.repositories.base import BaseRepo


class DDAStateRepo(BaseRepo[DDAStateModel]):
    """PostgreSQL implementation of DDAStateRepository protocol."""

    model_cls = DDAStateModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_session(self, session_id: UUID) -> DDAState | None:
        stmt = select(DDAStateModel).where(
            DDAStateModel.session_id == session_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return dda_state_model_to_domain(model) if model else None

    async def create(self, data: DDAStateCreate) -> DDAState:
        domain = DDAState(
            session_id=data.session_id,
            dialogue_stage=data.dialogue_stage,
        )
        model = dda_state_domain_to_model(domain)
        self._session.add(model)
        await self._session.flush()
        return dda_state_model_to_domain(model)

    async def update(self, state: DDAState) -> DDAState:
        stmt = select(DDAStateModel).where(
            DDAStateModel.session_id == state.session_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            msg = f"DDA state not found for session {state.session_id}"
            raise ValueError(msg)

        model.dda_level = state.dda_level
        model.operator_success_streak = state.operator_success_streak
        model.last_operator_messages = list(state.last_operator_messages)
        model.repetition_count = state.repetition_count
        model.dialogue_stage = state.dialogue_stage
        model.updated_at = state.updated_at

        await self._session.flush()
        return dda_state_model_to_domain(model)

    async def delete(self, session_id: UUID) -> None:
        stmt = delete(DDAStateModel).where(
            DDAStateModel.session_id == session_id
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def list_stale(self, older_than: datetime) -> list[DDAState]:
        stmt = select(DDAStateModel).where(
            DDAStateModel.updated_at < older_than
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [dda_state_model_to_domain(m) for m in models]

    async def delete_stale(self, older_than: datetime) -> int:
        stmt = delete(DDAStateModel).where(
            DDAStateModel.updated_at < older_than
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]
