"""
Tests for Redis Semantic Cache.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from chatopsllm_api.cache.semantic_cache import SemanticCache, _cosine_similarity


# ---------------------------------------------------------------------------
# Unit tests – cosine similarity helper
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert _cosine_similarity(a, b) == 0.0


# ---------------------------------------------------------------------------
# Unit tests – SemanticCache (Redis mocked)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_redis():
    with patch("chatopsllm_api.cache.semantic_cache.redis.Redis") as MockRedis:
        instance = MagicMock()
        MockRedis.return_value = instance
        yield instance


class TestSemanticCache:
    def test_ping_returns_true_when_redis_ok(self, mock_redis):
        mock_redis.ping.return_value = True
        cache = SemanticCache()
        assert cache.ping() is True

    def test_set_stores_json_with_ttl(self, mock_redis):
        cache = SemanticCache()
        cache.set("hello world", "some response")
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        # key starts with namespace prefix
        assert call_args[0][0].startswith("semantic_cache:")
        payload = json.loads(call_args[0][2])
        assert payload["response"] == "some response"
        assert "embedding" in payload

    def test_get_returns_none_on_empty_store(self, mock_redis):
        mock_redis.scan_iter.return_value = iter([])
        cache = SemanticCache()
        result = cache.get("any prompt")
        assert result is None

    def test_get_returns_cached_on_exact_match(self, mock_redis):
        cache = SemanticCache()
        prompt = "What is LiteLLM?"
        embedding = cache._embed(prompt)
        stored = json.dumps({"embedding": embedding, "response": "LiteLLM is a proxy."})

        mock_redis.scan_iter.return_value = iter(["semantic_cache:abc"])
        mock_redis.get.return_value = stored

        result = cache.get(prompt)
        assert result == "LiteLLM is a proxy."

    def test_flush_deletes_all_namespace_keys(self, mock_redis):
        mock_redis.scan_iter.return_value = iter(["semantic_cache:a", "semantic_cache:b"])
        cache = SemanticCache()
        cache.flush()
        assert mock_redis.delete.call_count == 2
