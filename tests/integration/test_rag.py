"""Tests for RAG service — uses mocked QdrantStore + embedding API."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_store():
    """Create a properly mocked QdrantStore (helper, not a fixture)."""
    store = MagicMock()
    store.search = AsyncMock(return_value=[{"id": "s-001", "score": 0.95, "payload": {"text": "mock"}}])
    store.ensure_collection = AsyncMock()
    store.upsert_script = AsyncMock()
    store.upsert_scripts_batch = AsyncMock()
    store.delete_script = AsyncMock()
    store.collection_info = AsyncMock(return_value={"status": "green", "vectors_count": 10, "segments_count": 1})
    store.close = AsyncMock()
    return store


class TestRAGService:
    """Tests for RAG service (mocked Qdrant)."""

    @pytest.mark.asyncio
    async def test_retrieve_context_empty_query(self):
        """Empty query returns empty list even with a store."""
        from infrastructure.qdrant.rag_service import RAGService

        service = RAGService(store=_make_store())
        results = await service.retrieve_context(query="", top_k=3)
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_context_with_mocked_store(self):
        """Non-empty query with mocked embedding + store returns results."""
        from infrastructure.qdrant.rag_service import RAGService

        store = _make_store()
        service = RAGService(store=store)

        # Mock the embedding API call
        with patch.object(service, "_get_embedding", return_value=[0.1] * 768):
            results = await service.retrieve_context(query="angry customer", top_k=3)

        assert len(results) == 1
        assert results[0]["id"] == "s-001"
        assert results[0]["score"] == 0.95
        store.search.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_index_no_error(self):
        """Calling ensure_index should delegate to store."""
        from infrastructure.qdrant.rag_service import RAGService

        store = _make_store()
        service = RAGService(store=store)
        await service.ensure_index()
        store.ensure_collection.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_index_no_store(self):
        """ensure_index with store=None is a no-op (not crash)."""
        from infrastructure.qdrant.rag_service import RAGService

        service = RAGService(store=None)
        await service.ensure_index()  # must not raise

    @pytest.mark.asyncio
    async def test_retrieve_context_no_store(self):
        """retrieve_context with store=None returns empty list."""
        from infrastructure.qdrant.rag_service import RAGService

        service = RAGService(store=None)
        results = await service.retrieve_context(query="anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_index_script_delegates(self):
        """index_script calls _get_embedding + store.upsert_script."""
        from uuid import UUID

        from infrastructure.qdrant.rag_service import RAGService

        store = _make_store()
        service = RAGService(store=store)

        with patch.object(service, "_get_embedding", return_value=[0.5] * 768):
            await service.index_script(
                script_id=UUID(int=42),
                text="Handle angry customer",
                metadata={"source": "test"},
            )

        store.upsert_script.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_index_script_no_store(self):
        """index_script with store=None is a no-op."""
        from uuid import UUID

        from infrastructure.qdrant.rag_service import RAGService

        service = RAGService(store=None)
        await service.index_script(script_id=UUID(int=1), text="test")
        # must not raise


class TestQdrantStore:
    """Tests for Qdrant wrapper (no server — validates API calls fail gracefully)."""

    @pytest.mark.asyncio
    async def test_search_no_server(self):
        """Search without a running Qdrant server raises appropriate error."""
        from infrastructure.qdrant.client import QdrantStore

        store = QdrantStore(host="127.0.0.1", port=19999)
        with pytest.raises(Exception):
            await store.search(query_vector=[0.1] * 768)
        await store.close()
