"""Mappers between BadgeModel/UserBadgeModel and domain entities."""

from core.entities.badge import Badge, UserBadge
from infrastructure.postgres.models.badge import BadgeModel, UserBadgeModel


def badge_model_to_domain(model: BadgeModel) -> Badge:
    """Convert ORM model to domain entity."""
    return Badge(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        description=model.description,
        icon_url=model.icon_url,
        criteria=model.criteria,
        xp_reward=model.xp_reward,
        is_hidden=model.is_hidden,
        created_at=model.created_at,
    )


def badge_domain_to_model(domain: Badge) -> BadgeModel:
    """Convert domain entity to ORM model."""
    return BadgeModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        name=domain.name,
        description=domain.description,
        icon_url=domain.icon_url,
        criteria=domain.criteria,
        xp_reward=domain.xp_reward,
        is_hidden=domain.is_hidden,
        created_at=domain.created_at,
    )


def user_badge_model_to_domain(model: UserBadgeModel) -> UserBadge:
    """Convert ORM model to UserBadge domain entity."""
    return UserBadge(
        id=model.id,
        user_id=model.user_id,
        badge_id=model.badge_id,
        awarded_at=model.awarded_at,
    )


def user_badge_domain_to_model(domain: UserBadge) -> UserBadgeModel:
    """Convert UserBadge domain entity to ORM model."""
    return UserBadgeModel(
        id=domain.id,
        user_id=domain.user_id,
        badge_id=domain.badge_id,
        awarded_at=domain.awarded_at,
    )
