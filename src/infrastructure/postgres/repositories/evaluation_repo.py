"""PostgreSQL implementation of EvaluationRepository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.evaluation import Evaluation, EvaluationCreate
from core.exceptions import NotFoundError
from infrastructure.postgres.mappers.evaluation_mapper import (
    evaluation_domain_to_model,
    evaluation_model_to_domain,
)
from infrastructure.postgres.models.evaluation import EvaluationModel
from infrastructure.postgres.repositories.base import BaseRepo


class EvaluationRepo(BaseRepo[EvaluationModel]):
    """PostgreSQL implementation of EvaluationRepository protocol."""

    model_cls = EvaluationModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, evaluation_id: UUID) -> Evaluation | None:
        model = await self._get_by_id(self._session, evaluation_id)
        return evaluation_model_to_domain(model) if model else None

    async def get_by_session(self, session_id: UUID) -> Evaluation | None:
        stmt = select(EvaluationModel).where(EvaluationModel.session_id == session_id)
        result = await self._safe_call("get_by_session", self._session.execute(stmt))
        model = result.scalars().first()
        return evaluation_model_to_domain(model) if model else None

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Evaluation]:
        stmt = (
            select(EvaluationModel)
            .where(EvaluationModel.user_id == user_id)
            .order_by(EvaluationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._safe_call("list_by_user", self._session.execute(stmt))
        models = list(result.scalars().all())
        return [evaluation_model_to_domain(m) for m in models]

    async def create(self, data: EvaluationCreate) -> Evaluation:
        domain = Evaluation(
            session_id=data.session_id,
            user_id=data.user_id,
            overall_score=data.overall_score,
            script_adherence=data.script_adherence,
            tone_score=data.tone_score,
            empathy_score=data.empathy_score,
            objection_handling=data.objection_handling,
            completeness_score=data.completeness_score,
        )
        model = evaluation_domain_to_model(domain)
        self._session.add(model)
        await self._session.flush()
        return evaluation_model_to_domain(model)

    async def update(self, evaluation: Evaluation) -> Evaluation:
        existing = await self._get_by_id(self._session, evaluation.id)
        if existing is None:
            msg = "Evaluation"
            raise NotFoundError(msg, str(evaluation.id))
        model = evaluation_domain_to_model(evaluation)
        await self._session.merge(model)
        await self._session.flush()
        return evaluation

    async def delete(self, evaluation_id: UUID) -> None:
        await self._delete(self._session, evaluation_id)

    async def get_average_score(self, user_id: UUID) -> float:
        stmt = select(func.avg(EvaluationModel.overall_score)).where(
            EvaluationModel.user_id == user_id
        )
        result = await self._safe_call("get_average_score", self._session.execute(stmt))
        val = result.scalar()
        return float(val) if val is not None else 0.0
