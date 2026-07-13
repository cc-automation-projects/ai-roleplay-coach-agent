"""PostgreSQL implementation of XPTransactionRepository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.xp import XPTransaction
from infrastructure.postgres.mappers.xp_mapper import xp_domain_to_model, xp_model_to_domain
from infrastructure.postgres.models.xp import XPTransactionModel
from infrastructure.postgres.repositories.base import BaseRepo


class XPTransactionRepo(BaseRepo[XPTransactionModel]):
    """PostgreSQL implementation of XPTransactionRepository protocol."""

    model_cls = XPTransactionModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, txn: XPTransaction) -> XPTransaction:
        model = xp_domain_to_model(txn)
        self._session.add(model)
        await self._session.flush()
        return xp_model_to_domain(model)

    async def count_by_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).where(
            XPTransactionModel.user_id == user_id
        )
        result = await self._safe_call("count_by_user", self._session.execute(stmt))
        return int(result.scalar_one())

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[XPTransaction]:
        stmt = (
            select(XPTransactionModel)
            .where(XPTransactionModel.user_id == user_id)
            .order_by(XPTransactionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._safe_call("list_by_user", self._session.execute(stmt))
        models = list(result.scalars().all())
        return [xp_model_to_domain(m) for m in models]

    async def get_total_xp(self, user_id: UUID) -> int:
        stmt = select(func.coalesce(func.sum(XPTransactionModel.amount), 0)).where(
            XPTransactionModel.user_id == user_id
        )
        result = await self._safe_call("get_total_xp", self._session.execute(stmt))
        return int(result.scalar_one())
