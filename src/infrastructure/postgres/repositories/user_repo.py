"""PostgreSQL implementation of UserRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.user import User, UserCreate
from core.exceptions import NotFoundError
from infrastructure.postgres.mappers.user_mapper import user_domain_to_model, user_model_to_domain
from infrastructure.postgres.models.user import UserModel
from infrastructure.postgres.repositories.base import BaseRepo


class UserRepo(BaseRepo[UserModel]):
    """PostgreSQL implementation of UserRepository protocol."""

    model_cls = UserModel

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._get_by_id(self._session, user_id)
        return user_model_to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._safe_call("get_by_email", self._session.execute(stmt))
        model = result.scalars().first()
        return user_model_to_domain(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        models = await self._list_all(self._session, skip=skip, limit=limit)
        return [user_model_to_domain(m) for m in models]

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username),
        )
        model = result.scalars().first()
        return user_model_to_domain(model) if model else None

    async def create(self, data: UserCreate) -> User:
        domain = User(
            username=data.username,
            hashed_password=data.hashed_password,
            email=data.email,
            name=data.name,
            role=data.role,
        )
        model = user_domain_to_model(domain)
        self._session.add(model)
        await self._session.flush()
        return user_model_to_domain(model)

    async def update(self, user: User) -> User:
        existing = await self._get_by_id(self._session, user.id)
        if existing is None:
            msg = "User"
            raise NotFoundError(msg, str(user.id))
        model = user_domain_to_model(user)
        await self._session.merge(model)
        await self._session.flush()
        return user

    async def delete(self, user_id: UUID) -> None:
        await self._delete(self._session, user_id)

    async def count(self) -> int:
        return await self._count(self._session)

    async def get_leaderboard(self, limit: int = 10, skip: int = 0) -> list[User]:
        stmt = (
            select(UserModel)
            .where(UserModel.is_active.is_(True))
            .order_by(UserModel.xp_total.desc(), UserModel.name.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._safe_call("get_leaderboard", self._session.execute(stmt))
        models = list(result.scalars().all())
        return [user_model_to_domain(m) for m in models]
