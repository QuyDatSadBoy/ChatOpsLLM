"""
Tests for Qdrant vector store and RAG retriever.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# QdrantVectorStore tests (Qdrant client mocked)
# ---------------------------------------------------------------------------

class TestQdrantVectorStore:
    @patch("chatopsllm_api.rag.qdrant_store.QdrantClient")
    def test_upsert_returns_ids(self, MockClient):
        mock_instance = MagicMock()
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        MockClient.return_value = mock_instance

        from chatopsllm_api.rag.qdrant_store import QdrantVectorStore

        store = QdrantVectorStore()
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        payloads = [{"text": "a"}, {"text": "b"}]
        ids = store.upsert(vectors=vectors, payloads=payloads)

        assert len(ids) == 2
        assert mock_instance.upsert.called

    @patch("chatopsllm_api.rag.qdrant_store.QdrantClient")
    def test_search_returns_results(self, MockClient):
        mock_instance = MagicMock()
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        mock_hit = MagicMock(id="abc", score=0.9, payload={"text": "hello"})
        mock_instance.search.return_value = [mock_hit]
        MockClient.return_value = mock_instance

        from chatopsllm_api.rag.qdrant_store import QdrantVectorStore

        store = QdrantVectorStore()
        results = store.search(query_vector=[0.1] * 32)

        assert len(results) == 1
        assert results[0]["score"] == 0.9
        assert results[0]["payload"]["text"] == "hello"

    @patch("chatopsllm_api.rag.qdrant_store.QdrantClient")
    def test_upsert_raises_on_mismatched_lengths(self, MockClient):
        mock_instance = MagicMock()
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        MockClient.return_value = mock_instance

        from chatopsllm_api.rag.qdrant_store import QdrantVectorStore

        store = QdrantVectorStore()
        with pytest.raises(ValueError, match="same length"):
            store.upsert(vectors=[[0.1]], payloads=[{"text": "a"}, {"text": "b"}])


# ---------------------------------------------------------------------------
# QdrantRetriever tests
# ---------------------------------------------------------------------------

class TestQdrantRetriever:
    def test_retrieve_returns_documents(self):
        mock_store = MagicMock()
        mock_store.search.return_value = [{"id": "1", "score": 0.85, "payload": {"text": "doc1"}}]

        with patch(
            "chatopsllm_api.rag.retriever.embed_texts",
            new_callable=AsyncMock,
            return_value=[[0.1] * 32],
        ):
            from chatopsllm_api.rag.retriever import QdrantRetriever

            retriever = QdrantRetriever(store=mock_store)
            results = asyncio.run(retriever.retrieve("test query"))

        assert len(results) == 1
        assert results[0]["payload"]["text"] == "doc1"

    def test_ingest_calls_upsert(self):
        mock_store = MagicMock()
        mock_store.upsert.return_value = ["id1", "id2"]

        with patch(
            "chatopsllm_api.rag.retriever.embed_texts",
            new_callable=AsyncMock,
            return_value=[[0.1] * 32, [0.2] * 32],
        ):
            from chatopsllm_api.rag.retriever import QdrantRetriever

            retriever = QdrantRetriever(store=mock_store)
            ids = asyncio.run(retriever.ingest(texts=["text1", "text2"]))

        assert ids == ["id1", "id2"]
        mock_store.upsert.assert_called_once()
