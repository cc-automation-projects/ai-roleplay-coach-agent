"""Mapper between UserModel and User domain entity."""

from core.entities.user import User, UserRole
from infrastructure.postgres.models.user import UserModel


def user_model_to_domain(model: UserModel) -> User:
    """Convert ORM model to domain entity.

    Raises ValueError if required fields are None.
    """
    username = model.username
    if username is None:
        msg = "username is required on UserModel"
        raise ValueError(msg)
    hashed_password = model.hashed_password
    if hashed_password is None:
        msg = "hashed_password is required on UserModel"
        raise ValueError(msg)
    return User(
        id=model.id,
        tenant_id=model.tenant_id,
        username=username,
        hashed_password=hashed_password,
        email=model.email,
        name=model.name,
        role=UserRole(model.role),
        xp_total=model.xp_total,
        level=model.level,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_domain_to_model(domain: User) -> UserModel:
    """Convert domain entity to ORM model."""
    return UserModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        username=domain.username,
        hashed_password=domain.hashed_password,
        email=domain.email,
        name=domain.name,
        role=str(domain.role.value),
        xp_total=domain.xp_total,
        level=domain.level,
        is_active=domain.is_active,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
