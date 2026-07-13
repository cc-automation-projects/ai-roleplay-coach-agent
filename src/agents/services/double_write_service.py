"""DoubleWriteService — transactional write to PG + Qdrant.

Ensures data is always persisted to the primary store (PostgreSQL)
while the secondary store (Qdrant vector DB) is updated best-effort
with circuit-breaker protection to avoid cascading failures.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.exceptions import EntityNotFoundError
from core.services.circuit_breaker import CircuitBreakerRegistry, CircuitState
from core.utils import utcnow

if TYPE_CHECKING:
    from uuid import UUID

    from core.interfaces.repositories import ScenarioRepository
    from infrastructure.qdrant.rag_service import RAGService

logger = logging.getLogger(__name__)


class DoubleWriteService:
    """Coordinator for dual-write to PG + Qdrant.

    Usage
    -----
    .. code-block:: python

        service = DoubleWriteService(db_session, rag_service)
        await service.write_scenario(scenario_id, text)
    """

    def __init__(
        self,
        scenario_repo: ScenarioRepository,
        rag_service: RAGService,
        cb_registry: CircuitBreakerRegistry | None = None,
    ) -> None:
        self._scenario_repo = scenario_repo
        self._rag = rag_service
        self._cb = cb_registry or CircuitBreakerRegistry()

    # ── Scenario writes ─────────────────────────────────────────────────

    async def write_scenario(
        self,
        scenario_id: UUID,
        text: str,
        /,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a scenario script in PG **and** Qdrant.

        1. Update the scenario row in PostgreSQL.
        2. Index the embedding in Qdrant (best-effort with CB).

        If Qdrant is unreachable, the PG write is never rolled back
        (the data is safe).  A warning is logged for offline retry.
        """
        # Step 1 — PostgreSQL (always, primary store)
        scenario = await self._scenario_repo.get_by_id(scenario_id)
        if scenario is None:
            raise EntityNotFoundError(
                entity_type="Scenario",
                entity_id=str(scenario_id),
            )
        scenario.script_text = text  # type: ignore[assignment]
        scenario.updated_at = utcnow()
        await self._scenario_repo.update(scenario)

        # Step 2 — Qdrant (best-effort, CB-protected)
        cb = self._cb.get("qdrant")
        if cb.state == CircuitState.OPEN:
            logger.warning(
                "Qdrant CB is OPEN — skip indexing scenario %s "
                "(will retry on next successful write)",
                scenario_id,
            )
            return

        try:
            await self._rag.index_script(
                text=text,
                script_id=str(scenario_id),
                metadata=metadata,
            )
            cb.on_success()
            logger.debug(
                "Indexed scenario %s in Qdrant", scenario_id
            )
        except Exception:
            logger.exception(
                "Failed to index scenario %s in Qdrant "
                "(PG write succeeded)",
                scenario_id,
            )
            cb.on_failure()

    # ── Evaluation writes ───────────────────────────────────────────────

    async def write_evaluation(
        self,
        evaluation_id: UUID,
        user_id: UUID,
        session_id: UUID,
        score: float,
        /,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist an evaluation in PG **and** index it in Qdrant.

        Follows the same pattern as ``write_scenario`` — PG first,
        then best-effort Qdrant with CB protection.
        """
        # PG side is handled by the caller via the evaluation repo.
        # Here we only manage the Qdrant indexing as a best-effort
        # secondary write.
        cb = self._cb.get("qdrant")
        if cb.state == CircuitState.OPEN:
            logger.warning(
                "Qdrant CB is OPEN — skip indexing evaluation %s",
                evaluation_id,
            )
            return

        try:
            await self._rag.index_script(
                text=f"eval:{evaluation_id}:score={score}",
                script_id=str(evaluation_id),
                metadata={
                    "user_id": str(user_id),
                    "session_id": str(session_id),
                    "score": score,
                    "type": "evaluation",
                    **(metadata or {}),
                },
            )
            cb.on_success()
        except Exception:
            logger.exception("Failed to index evaluation %s in Qdrant", evaluation_id)
            cb.on_failure()

    # ── Batch / background sync ─────────────────────────────────────────

    async def sync_pending(
        self,
        pending_ids: list[UUID],
        /,
        *,
        texts: dict[UUID, str] | None = None,
        batch_size: int = 10,
    ) -> tuple[int, int]:
        """Retry indexing for IDs that were missed during outages.

        Args:
            pending_ids: List of scenario / evaluation IDs to re-index.
            texts: Optional map of ID → full text to index. If omitted
                the entries are skipped with a warning (caller must
                supply real text to avoid polluting the vector store).
            batch_size: How many to process per batch.

        Returns:
            (succeeded, failed) counts.
        """
        succeeded = 0
        failed = 0

        for i in range(0, len(pending_ids), batch_size):
            batch = pending_ids[i : i + batch_size]
            for sid in batch:
                text = (texts or {}).get(sid)
                if not text:
                    logger.warning(
                        "No text supplied for pending ID %s — skipping "
                        "(call sync_pending with ``texts`` to re-index)",
                        sid,
                    )
                    failed += 1
                    continue
                try:
                    await self._rag.index_script(
                        text=text,
                        script_id=str(sid),
                        metadata={"type": "retry"},
                    )
                    succeeded += 1
                except Exception:  # noqa: BLE001
                    logger.warning("Retry indexing failed for %s", sid)
                    failed += 1

        if failed:
            logger.warning(
                "Pending sync finished: %d succeeded, %d failed",
                succeeded,
                failed,
            )
        else:
            logger.info(
                "Pending sync finished: all %d succeeded", succeeded
            )

        return succeeded, failed
