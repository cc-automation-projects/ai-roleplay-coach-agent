"""Mapper between SessionModel and Session domain entity."""

from core.entities.scenario import DifficultyLevel, Psychotype
from core.entities.session import Session, SessionStatus, TranscriptEntry
from infrastructure.postgres.models.session import SessionModel


def transcript_model_to_domain(entry: dict) -> TranscriptEntry:
    """Convert raw dict transcript entry to domain entity."""
    return TranscriptEntry(
        speaker=entry["speaker"],
        text=entry["text"],
        timestamp=entry["timestamp"],
        metadata=entry.get("metadata", {}),
    )


def transcript_domain_to_model(entry: TranscriptEntry) -> dict:
    """Convert domain TranscriptEntry to a serializable dict."""
    return {
        "speaker": entry.speaker,
        "text": entry.text,
        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
        "metadata": entry.metadata,
    }


def session_model_to_domain(model: SessionModel) -> Session:
    """Convert ORM model to domain entity."""
    transcript_raw = model.transcript or []
    transcript = [transcript_model_to_domain(e) for e in transcript_raw]

    diff = DifficultyLevel(model.difficulty_at_start) if model.difficulty_at_start else None
    psych = Psychotype(model.psychotype_at_start) if model.psychotype_at_start else None

    return Session(
        id=model.id,
        tenant_id=model.tenant_id,
        user_id=model.user_id,
        scenario_id=model.scenario_id,
        status=SessionStatus(model.status),
        transcript=transcript,
        started_at=model.started_at,
        completed_at=model.completed_at,
        difficulty_at_start=diff,
        psychotype_at_start=psych,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def session_domain_to_model(domain: Session) -> SessionModel:
    """Convert domain entity to ORM model."""
    transcript_raw = [transcript_domain_to_model(e) for e in domain.transcript]

    diff = str(domain.difficulty_at_start.value) if domain.difficulty_at_start else None
    psych = str(domain.psychotype_at_start.value) if domain.psychotype_at_start else None

    return SessionModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        user_id=domain.user_id,
        scenario_id=domain.scenario_id,
        status=str(domain.status.value),
        transcript=transcript_raw,
        started_at=domain.started_at,
        completed_at=domain.completed_at,
        difficulty_at_start=diff,
        psychotype_at_start=psych,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
