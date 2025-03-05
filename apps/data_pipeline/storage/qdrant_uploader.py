"""
Qdrant uploader – persists embedded document chunks from the pipeline.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import os
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
_COLLECTION = os.getenv("QDRANT_COLLECTION", "chatopsllm_docs")
_VECTOR_SIZE = int(os.getenv("QDRANT_VECTOR_SIZE", "1536"))


def upload_to_qdrant(vectors: list[list[float]], payloads: list[dict]) -> list[str]:
    """
    Upsert *vectors* + *payloads* into the Qdrant collection.

    Returns the list of generated point IDs.
    """
    client = QdrantClient(url=_QDRANT_URL, api_key=_QDRANT_API_KEY)

    # Ensure collection exists
    existing = {c.name for c in client.get_collections().collections}
    if _COLLECTION not in existing:
        client.create_collection(
            collection_name=_COLLECTION,
            vectors_config=VectorParams(size=_VECTOR_SIZE, distance=Distance.COSINE),
        )

    ids = [str(uuid4()) for _ in vectors]
    points = [
        PointStruct(id=pid, vector=vec, payload=pay)
        for pid, vec, pay in zip(ids, vectors, payloads)
    ]
    client.upsert(collection_name=_COLLECTION, points=points)
    return ids
