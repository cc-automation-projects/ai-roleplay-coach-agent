"""Mappers between DDAStateModel and DDAState domain entity."""

from core.entities.dda_state import DDAState
from infrastructure.postgres.models.dda_state import DDAStateModel


def dda_state_model_to_domain(model: DDAStateModel) -> DDAState:
    """Convert ORM model to domain entity."""
    return DDAState(
        session_id=model.session_id,
        dda_level=model.dda_level,
        operator_success_streak=model.operator_success_streak,
        last_operator_messages=list(model.last_operator_messages or []),
        repetition_count=model.repetition_count,
        dialogue_stage=model.dialogue_stage,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def dda_state_domain_to_model(domain: DDAState) -> DDAStateModel:
    """Convert domain entity to ORM model."""
    return DDAStateModel(
        session_id=domain.session_id,
        dda_level=domain.dda_level,
        operator_success_streak=domain.operator_success_streak,
        last_operator_messages=list(domain.last_operator_messages),
        repetition_count=domain.repetition_count,
        dialogue_stage=domain.dialogue_stage,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
