"""Mapper between ScenarioModel and Scenario domain entity."""

from core.entities.scenario import DifficultyLevel, Psychotype, Scenario
from infrastructure.postgres.models.scenario import ScenarioModel


def scenario_model_to_domain(model: ScenarioModel) -> Scenario:
    """Convert ORM model to domain entity."""
    return Scenario(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        description=model.description,
        difficulty=DifficultyLevel(model.difficulty),
        psychotype=Psychotype(model.psychotype),
        script_ref=model.script_ref,
        script_text=model.script_text,
        tags=model.tags or [],
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def scenario_domain_to_model(domain: Scenario) -> ScenarioModel:
    """Convert domain entity to ORM model."""
    return ScenarioModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        name=domain.name,
        description=domain.description,
        difficulty=str(domain.difficulty.value),
        psychotype=str(domain.psychotype.value),
        script_ref=domain.script_ref,
        script_text=domain.script_text,
        tags=domain.tags,
        is_active=domain.is_active,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
