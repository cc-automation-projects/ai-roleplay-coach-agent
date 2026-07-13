"""Qdrant vector store client for RAG-based script retrieval."""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import Distance, VectorParams

if TYPE_CHECKING:
    from uuid import UUID

_COLLECTION_NAME = "coach_scripts"
_DEFAULT_VECTOR_SIZE = 768  # fallback if env not set


class QdrantStore:
    """Wrapper around Qdrant for script embedding storage and search."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        *,
        vector_size: int | None = None,
    ) -> None:
        host = host or os.environ.get("QDRANT_HOST", "localhost")
        # AsyncQdrantClient uses HTTP REST (port 6333 by default)
        http_port = port or int(os.environ.get("QDRANT_HTTP_PORT", "6333"))
        self._vector_size = vector_size or int(
            os.environ.get("VECTOR_SIZE", str(_DEFAULT_VECTOR_SIZE))
        )
        self._client = AsyncQdrantClient(
            host=host,
            port=http_port,
        )

    async def ensure_collection(self) -> None:
        """Create the collection if it does not exist."""
        collections = await self._client.get_collections()
        names = {c.name for c in collections.collections}
        if _COLLECTION_NAME not in names:
            await self._client.create_collection(
                collection_name=_COLLECTION_NAME,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )

    async def upsert_script(
        self,
        script_id: UUID,
        embedding: list[float],
        payload: dict | None = None,
    ) -> None:
        """Insert or update a single script embedding."""
        point_id = str(script_id)
        point = qmodels.PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload or {},
        )
        await self._client.upsert(
            collection_name=_COLLECTION_NAME,
            points=[point],
        )

    async def upsert_scripts_batch(
        self,
        embeddings: list[tuple[UUID, list[float], dict]],
    ) -> None:
        """Batch upsert multiple script embeddings."""
        points = [
            qmodels.PointStruct(id=str(sid), vector=emb, payload=pld or {})
            for sid, emb, pld in embeddings
        ]
        await self._client.upsert(
            collection_name=_COLLECTION_NAME,
            points=points,
        )

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float | None = 0.7,
    ) -> list[dict]:
        """Search for similar scripts by vector."""
        hits = await self._client.search(
            collection_name=_COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in hits
        ]

    async def delete_script(self, script_id: UUID) -> None:
        """Remove a script embedding by ID."""
        await self._client.delete(
            collection_name=_COLLECTION_NAME,
            points_selector=qmodels.PointIdsList(
                points=[str(script_id)],
            ),
        )

    async def collection_info(self) -> dict:
        """Return collection statistics."""
        info = await self._client.get_collection(collection_name=_COLLECTION_NAME)
        return {
            "status": str(info.status),
            "vectors_count": info.vectors_count,
            "segments_count": info.segments_count,
        }

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()

    def close_sync(self) -> None:
        """Synchronous wrapper for cleanup in __del__."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                task = loop.create_task(self.close())
                task.add_done_callback(lambda _t: None)
                return
        except RuntimeError:
            pass
        asyncio.run(self.close())
