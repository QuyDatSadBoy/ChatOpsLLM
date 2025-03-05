"""
Qdrant vector-store client wrapper.

Provides a thin, testable interface around ``qdrant-client`` for storing and
querying document embeddings used by the RAG pipeline.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import os
from typing import Optional
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from chatopsllm_api import logger

_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "chatopsllm_docs")
_VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))


class QdrantVectorStore:
    """Thin wrapper around ``QdrantClient`` for collection management and search."""

    def __init__(
        self,
        url: str = _QDRANT_URL,
        api_key: Optional[str] = _QDRANT_API_KEY,
        collection_name: str = _COLLECTION_NAME,
        vector_size: int = _VECTOR_SIZE,
    ) -> None:
        self._client = QdrantClient(url=url, api_key=api_key)
        self._collection = collection_name
        self._vector_size = vector_size
        self._ensure_collection()

    # ------------------------------------------------------------------
    # Collection lifecycle
    # ------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        """Create the collection if it does not already exist."""
        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"[Qdrant] Created collection '{self._collection}'")
        else:
            logger.info(f"[Qdrant] Collection '{self._collection}' already exists")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert(self, vectors: list[list[float]], payloads: list[dict]) -> list[str]:
        """
        Upsert *vectors* with associated *payloads* into the collection.

        Returns the list of generated point IDs.
        """
        if len(vectors) != len(payloads):
            raise ValueError("vectors and payloads must have the same length")

        ids = [str(uuid4()) for _ in vectors]
        points = [
            PointStruct(id=pid, vector=vec, payload=pay)
            for pid, vec, pay in zip(ids, vectors, payloads)
        ]
        self._client.upsert(collection_name=self._collection, points=points)
        logger.info(f"[Qdrant] Upserted {len(points)} points")
        return ids

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> list[dict]:
        """
        Return the top-*k* most similar documents for *query_vector*.

        Each result is a dict with keys ``id``, ``score``, and ``payload``.
        """
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]

    def delete(self, point_ids: list[str]) -> None:
        """Remove points by ID."""
        from qdrant_client.http.models import PointIdsList

        self._client.delete(
            collection_name=self._collection,
            points_selector=PointIdsList(points=point_ids),
        )
        logger.info(f"[Qdrant] Deleted {len(point_ids)} points")
