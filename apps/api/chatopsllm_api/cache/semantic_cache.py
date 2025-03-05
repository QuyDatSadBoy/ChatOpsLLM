"""
Redis Semantic Cache for LLM responses.

Implements vector-similarity-based caching using Redis as the backing store.
Embeddings are computed for each prompt; if a sufficiently similar prompt has
been answered before, the cached response is returned without calling the LLM.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import hashlib
import json
import os
from typing import Optional

import redis

from chatopsllm_api import logger

_CACHE_TTL_SECONDS = int(os.getenv("REDIS_CACHE_TTL", "3600"))
_SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.92"))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    """
    Semantic cache backed by Redis.

    Flow
    ----
    1. ``get(prompt)``  – compute embedding → scan stored keys → return cached
       response if cosine similarity ≥ threshold.
    2. ``set(prompt, response)`` – store (embedding, response) pair in Redis
       with a TTL.
    """

    def __init__(
        self,
        host: str = os.getenv("REDIS_HOST", "localhost"),
        port: int = int(os.getenv("REDIS_PORT", "6379")),
        db: int = int(os.getenv("REDIS_CACHE_DB", "1")),
        password: Optional[str] = os.getenv("REDIS_PASSWORD"),
    ) -> None:
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        self._namespace = "semantic_cache"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        """
        Lightweight deterministic embedding for unit-testing / local dev.

        In production this should be replaced by a real embedding model
        (e.g. ``text-embedding-3-small`` via the OpenAI-compatible LiteLLM
        proxy, or a self-hosted sentence-transformers model via BentoML/vLLM).
        """
        # Use SHA-256 hash bytes as a reproducible 32-dim pseudo-embedding.
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in digest]

    def _cache_key(self, prompt_hash: str) -> str:
        return f"{self._namespace}:{prompt_hash}"

    def _prompt_hash(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, prompt: str) -> Optional[str]:
        """
        Return a cached response for *prompt* if a semantically similar entry
        exists; otherwise return ``None``.
        """
        try:
            query_emb = self._embed(prompt)
            pattern = f"{self._namespace}:*"
            for key in self._client.scan_iter(pattern):
                raw = self._client.get(key)
                if raw is None:
                    continue
                entry = json.loads(raw)
                similarity = _cosine_similarity(query_emb, entry["embedding"])
                if similarity >= _SIMILARITY_THRESHOLD:
                    logger.info(f"[SemanticCache] HIT  key={key} similarity={similarity:.4f}")
                    return entry["response"]
        except redis.RedisError as exc:
            logger.warning(f"[SemanticCache] Redis error during get: {exc}")
        return None

    def set(self, prompt: str, response: str) -> None:
        """Cache *response* for *prompt*."""
        try:
            key = self._cache_key(self._prompt_hash(prompt))
            payload = json.dumps({"embedding": self._embed(prompt), "response": response})
            self._client.setex(key, _CACHE_TTL_SECONDS, payload)
            logger.info(f"[SemanticCache] SET  key={key}")
        except redis.RedisError as exc:
            logger.warning(f"[SemanticCache] Redis error during set: {exc}")

    def delete(self, prompt: str) -> None:
        """Remove a cached entry for *prompt*."""
        try:
            key = self._cache_key(self._prompt_hash(prompt))
            self._client.delete(key)
        except redis.RedisError as exc:
            logger.warning(f"[SemanticCache] Redis error during delete: {exc}")

    def flush(self) -> None:
        """Flush **all** entries under the semantic-cache namespace."""
        try:
            for key in self._client.scan_iter(f"{self._namespace}:*"):
                self._client.delete(key)
            logger.info("[SemanticCache] Flushed all entries")
        except redis.RedisError as exc:
            logger.warning(f"[SemanticCache] Redis error during flush: {exc}")

    def ping(self) -> bool:
        """Return ``True`` if the Redis server is reachable."""
        try:
            return self._client.ping()
        except redis.RedisError:
            return False
