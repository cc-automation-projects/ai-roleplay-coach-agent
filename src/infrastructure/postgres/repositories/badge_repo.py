"""PostgreSQL implementation of BadgeRepository."""

from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.badge import Badge, BadgeCreate, UserBadge
from infrastructure.postgres.mappers.badge_mapper import (
    badge_domain_to_model,
    badge_model_to_domain,
    user_badge_domain_to_model,
    user_badge_model_to_domain,
)
from infrastructure.postgres.models.badge import BadgeModel, UserBadgeModel
from infrastructure.postgres.repositories.base import BaseRepo


class BadgeRepo(BaseRepo[BadgeModel]):
    """PostgreSQL implementation of BadgeRepository protocol."""

    model_cls = BadgeModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, badge_id: UUID) -> Badge | None:
        model = await self._get_by_id(self._session, badge_id)
        return badge_model_to_domain(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Badge]:
        models = await self._list_all(self._session, skip=skip, limit=limit)
        return [badge_model_to_domain(m) for m in models]

    async def create(self, data: BadgeCreate) -> Badge:
        domain = Badge(
            name=data.name,
            description=data.description,
            icon_url=data.icon_url,
            criteria=data.criteria,
            xp_reward=data.xp_reward,
            is_hidden=data.is_hidden,
        )
        model = badge_domain_to_model(domain)
        self._session.add(model)
        await self._session.flush()
        return badge_model_to_domain(model)

    async def award_to_user(self, user_badge: UserBadge) -> UserBadge:
        model = user_badge_domain_to_model(user_badge)
        self._session.add(model)
        await self._session.flush()
        return user_badge_model_to_domain(model)

    async def get_user_badges(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Badge]:
        stmt = (
            select(BadgeModel)
            .join(UserBadgeModel, BadgeModel.id == UserBadgeModel.badge_id)
            .where(UserBadgeModel.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self._safe_call("get_user_badges", self._session.execute(stmt))
        models = list(result.scalars().all())
        return [badge_model_to_domain(m) for m in models]

    async def count_user_badges(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(BadgeModel)
            .join(UserBadgeModel, BadgeModel.id == UserBadgeModel.badge_id)
            .where(UserBadgeModel.user_id == user_id)
        )
        result = await self._safe_call("count_user_badges", self._session.execute(stmt))
        return result.scalar_one()

    async def has_user_badge(self, user_id: UUID, badge_id: UUID) -> bool:
        stmt = select(
            exists().where(
                UserBadgeModel.user_id == user_id,
                UserBadgeModel.badge_id == badge_id,
            )
        )
        result = await self._safe_call("has_user_badge", self._session.execute(stmt))
        return result.scalar_one()
