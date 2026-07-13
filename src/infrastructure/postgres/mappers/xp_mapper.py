"""Mappers between XPTransactionModel/MetricModel and domain entities."""

from core.entities.xp import Metric, MetricType, XPReason, XPTransaction
from infrastructure.postgres.models.xp import MetricModel, XPTransactionModel


def xp_model_to_domain(model: XPTransactionModel) -> XPTransaction:
    """Convert ORM model to domain entity."""
    return XPTransaction(
        id=model.id,
        user_id=model.user_id,
        amount=model.amount,
        reason=XPReason(model.reason),
        reference_id=model.reference_id,
        created_at=model.created_at,
    )


def xp_domain_to_model(domain: XPTransaction) -> XPTransactionModel:
    """Convert domain entity to ORM model."""
    return XPTransactionModel(
        id=domain.id,
        user_id=domain.user_id,
        amount=domain.amount,
        reason=str(domain.reason.value),
        reference_id=domain.reference_id,
        created_at=domain.created_at,
    )


def metric_model_to_domain(model: MetricModel) -> Metric:
    """Convert ORM model to domain entity."""
    return Metric(
        id=model.id,
        user_id=model.user_id,
        metric_type=MetricType(model.metric_type),
        value=model.value,
        recorded_at=model.recorded_at,
    )


def metric_domain_to_model(domain: Metric) -> MetricModel:
    """Convert domain entity to ORM model."""
    return MetricModel(
        id=domain.id,
        user_id=domain.user_id,
        metric_type=str(domain.metric_type.value),
        value=domain.value,
        recorded_at=domain.recorded_at,
    )
