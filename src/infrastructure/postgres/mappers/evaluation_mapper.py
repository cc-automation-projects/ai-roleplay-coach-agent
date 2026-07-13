"""Mapper between EvaluationModel and Evaluation domain entity."""

from core.entities.evaluation import Evaluation
from infrastructure.postgres.models.evaluation import EvaluationModel


def evaluation_model_to_domain(model: EvaluationModel) -> Evaluation:
    """Convert ORM model to domain entity."""
    return Evaluation(
        id=model.id,
        tenant_id=model.tenant_id,
        session_id=model.session_id,
        user_id=model.user_id,
        overall_score=model.overall_score,
        script_adherence=model.script_adherence,
        tone_score=model.tone_score,
        empathy_score=model.empathy_score,
        objection_handling=model.objection_handling,
        completeness_score=model.completeness_score,
        praise_text=model.praise_text,
        growth_text=model.growth_text,
        closing_text=model.closing_text,
        script_citations=model.script_citations or [],
        gaming_detected=model.gaming_detected,
        gaming_notes=model.gaming_notes,
        created_at=model.created_at,
    )


def evaluation_domain_to_model(domain: Evaluation) -> EvaluationModel:
    """Convert domain entity to ORM model."""
    return EvaluationModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        session_id=domain.session_id,
        user_id=domain.user_id,
        overall_score=domain.overall_score,
        script_adherence=domain.script_adherence,
        tone_score=domain.tone_score,
        empathy_score=domain.empathy_score,
        objection_handling=domain.objection_handling,
        completeness_score=domain.completeness_score,
        praise_text=domain.praise_text,
        growth_text=domain.growth_text,
        closing_text=domain.closing_text,
        script_citations=list(domain.script_citations),
        gaming_detected=domain.gaming_detected,
        gaming_notes=domain.gaming_notes,
        created_at=domain.created_at,
    )
