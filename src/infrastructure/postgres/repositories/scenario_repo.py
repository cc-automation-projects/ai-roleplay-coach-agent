"""PostgreSQL implementation of ScenarioRepository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.scenario import Scenario, ScenarioCreate
from core.exceptions import NotFoundError
from infrastructure.postgres.mappers.scenario_mapper import (
    scenario_domain_to_model,
    scenario_model_to_domain,
)
from infrastructure.postgres.models.scenario import ScenarioModel
from infrastructure.postgres.repositories.base import BaseRepo


class ScenarioRepo(BaseRepo[ScenarioModel]):
    """PostgreSQL implementation of ScenarioRepository protocol."""

    model_cls = ScenarioModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, scenario_id: UUID) -> Scenario | None:
        model = await self._get_by_id(self._session, scenario_id)
        return scenario_model_to_domain(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Scenario]:
        models = await self._list_all(self._session, skip=skip, limit=limit)
        return [scenario_model_to_domain(m) for m in models]

    async def create(self, data: ScenarioCreate) -> Scenario:
        domain = Scenario(
            name=data.name,
            description=data.description,
            difficulty=data.difficulty,
            psychotype=data.psychotype,
            script_ref=data.script_ref,
            script_text=data.script_text,
            tags=data.tags,
        )
        model = scenario_domain_to_model(domain)
        self._session.add(model)
        await self._session.flush()
        return scenario_model_to_domain(model)

    async def update(self, scenario: Scenario) -> Scenario:
        existing = await self._get_by_id(self._session, scenario.id)
        if existing is None:
            msg = "Scenario"
            raise NotFoundError(msg, str(scenario.id))
        model = scenario_domain_to_model(scenario)
        await self._session.merge(model)
        await self._session.flush()
        return scenario

    async def delete(self, scenario_id: UUID) -> None:
        await self._delete(self._session, scenario_id)

    async def count(self) -> int:
        return await self._count(self._session)

    async def list_by_difficulty(
        self, difficulty: str, skip: int = 0, limit: int = 100
    ) -> list[Scenario]:
        stmt = (
            select(ScenarioModel)
            .where(ScenarioModel.difficulty == difficulty)
            .where(ScenarioModel.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        result = await self._safe_call("list_by_difficulty", self._session.execute(stmt))
        models = list(result.scalars().all())
        return [scenario_model_to_domain(m) for m in models]

    async def count_by_difficulty(self, difficulty: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ScenarioModel)
            .where(ScenarioModel.difficulty == difficulty)
            .where(ScenarioModel.is_active.is_(True))
        )
        result = await self._safe_call("count_by_difficulty", self._session.execute(stmt))
        return result.scalar_one()
