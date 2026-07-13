"""RAG service — retrieves script context for agents using Qdrant."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import httpx

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from uuid import UUID

    from infrastructure.qdrant.client import QdrantStore

_DEFAULT_TOP_K = 3
_DEFAULT_THRESHOLD = 0.65


class RAGService:
    """Retrieval-Augmented Generation service for script context."""

    def __init__(self, store: QdrantStore | None = None) -> None:
        self._store = store
        self._embedding_url = os.environ.get(
            "EMBEDDING_URL",
            "http://localhost:8000/v1/embeddings",
        )

    async def ensure_index(self) -> None:
        """Ensure the Qdrant collection exists."""
        if self._store is None:
            return
        await self._store.ensure_collection()

    async def retrieve_context(
        self,
        query: str,
        top_k: int = _DEFAULT_TOP_K,
        score_threshold: float | None = _DEFAULT_THRESHOLD,
    ) -> list[dict]:
        """Retrieve relevant script chunks for a query."""
        if self._store is None:
            return []
        vector = await self._get_embedding(query)
        if not vector:
            return []
        return await self._store.search(
            query_vector=vector,
            top_k=top_k,
            score_threshold=score_threshold,
        )

    async def index_script(
        self,
        script_id: UUID,
        text: str,
        metadata: dict | None = None,
    ) -> None:
        """Generate embedding for a script and index it in Qdrant."""
        if self._store is None:
            return
        vector = await self._get_embedding(text)
        if not vector:
            return
        payload = {
            "text": text,
            **(metadata or {}),
        }
        await self._store.upsert_script(
            script_id=script_id,
            embedding=vector,
            payload=payload,
        )

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Call the external embedding API (vLLM / OpenAI-compatible)."""
        if not text.strip():
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self._embedding_url,
                    json={
                        "input": text,
                        "model": os.environ.get(
                            "EMBEDDING_MODEL", "intfloat/multilingual-e5-large"
                        ),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
        except httpx.RequestError:
            logger.exception("Embedding API request failed")
            return None
        except httpx.HTTPStatusError:
            logger.exception("Embedding API returned an error")
            return None
        except Exception:
            logger.exception("Unexpected error in _get_embedding")
            return None
