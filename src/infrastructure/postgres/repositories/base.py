"""Base repository mixin with common CRUD helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import InfrastructureError

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

M = TypeVar("M")

logger = logging.getLogger(__name__)


class BaseRepo[M]:
    """Generic CRUD operations for a SQLAlchemy model."""

    model_cls: type[M]

    async def _safe_call[T](self, description: str, coro: object) -> T:
        """Wrap a DB awaitable, converting SQLAlchemyError → InfrastructureError."""
        try:
            return await coro  # type: ignore[misc]
        except SQLAlchemyError:
            logger.exception("DB error in %s", description)
            msg = f"Database operation '{description}' failed"
            raise InfrastructureError(msg) from None

    async def _get_by_id(self, session: AsyncSession, entity_id: UUID) -> M | None:
        """Fetch a single record by primary key."""
        stmt = select(self.model_cls).where(
            self.model_cls.id == entity_id  # type: ignore[attr-defined]
        )
        result = await self._safe_call("_get_by_id", session.execute(stmt))
        return result.scalars().first()

    async def _list_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[M]:
        """Fetch paginated records."""
        stmt = select(self.model_cls).offset(skip).limit(limit)
        result = await self._safe_call("_list_all", session.execute(stmt))
        return list(result.scalars().all())

    async def _count(self, session: AsyncSession) -> int:
        """Count all records."""
        stmt = select(func.count()).select_from(self.model_cls)
        result = await self._safe_call("_count", session.execute(stmt))
        return result.scalar_one()

    async def _delete(self, session: AsyncSession, entity_id: UUID) -> None:
        """Delete a record by primary key."""
        obj = await self._get_by_id(session, entity_id)
        if obj is not None:
            await self._safe_call("_delete", session.delete(obj))
