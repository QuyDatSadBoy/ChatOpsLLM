"""
RAG Retriever – embeds the query and fetches relevant context from Qdrant.

Combines ``embeddings.py`` and ``qdrant_store.py`` into a single retrieve()
call that is used by the ConversationHandler to augment prompts with
document context before sending them to LiteLLM.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

from __future__ import annotations

import os
from typing import Optional

from chatopsllm_api import logger
from chatopsllm_api.rag.embeddings import embed_texts
from chatopsllm_api.rag.qdrant_store import QdrantVectorStore

_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.7"))


class QdrantRetriever:
    """
    High-level RAG retriever.

    Usage
    -----
    ::

        retriever = QdrantRetriever()
        docs = await retriever.retrieve("What is LiteLLM?")
        context = "\\n\\n".join(d["payload"]["text"] for d in docs)
    """

    def __init__(
        self,
        store: Optional[QdrantVectorStore] = None,
        top_k: int = _TOP_K,
        score_threshold: float = _SCORE_THRESHOLD,
    ) -> None:
        self._store = store or QdrantVectorStore()
        self._top_k = top_k
        self._score_threshold = score_threshold

    async def retrieve(self, query: str) -> list[dict]:
        """
        Embed *query* and return the *top_k* most relevant documents from
        Qdrant whose similarity score is ≥ *score_threshold*.
        """
        vectors = await embed_texts(query)
        if not vectors:
            return []
        results = self._store.search(
            query_vector=vectors[0],
            top_k=self._top_k,
            score_threshold=self._score_threshold,
        )
        logger.info(f"[Retriever] Retrieved {len(results)} docs for query='{query[:60]}…'")
        return results

    async def ingest(self, texts: list[str], metadatas: Optional[list[dict]] = None) -> list[str]:
        """
        Embed and store *texts* in Qdrant.

        Parameters
        ----------
        texts:
            Plain-text document chunks.
        metadatas:
            Optional list of payload dicts aligned with *texts*. Each dict
            MUST contain at least a ``"text"`` key with the original chunk.

        Returns
        -------
        List of generated Qdrant point IDs.
        """
        if metadatas is None:
            metadatas = [{"text": t} for t in texts]

        vectors = await embed_texts(texts)
        ids = self._store.upsert(vectors=vectors, payloads=metadatas)
        logger.info(f"[Retriever] Ingested {len(ids)} documents")
        return ids
