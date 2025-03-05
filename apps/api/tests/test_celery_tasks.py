"""
Tests for Celery tasks.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGenerateChatResponseTask:
    def test_returns_cached_response_when_cache_hits(self):
        """If the semantic cache has a hit, the LLM should NOT be called."""
        with patch(
            "chatopsllm_api.worker.tasks._semantic_cache.get",
            return_value="cached answer",
        ):
            from chatopsllm_api.worker.tasks import generate_chat_response_task

            # Run synchronously via .apply() (no broker needed)
            result = generate_chat_response_task.apply(
                kwargs={"prompt": "hello", "model": "test-model"}
            )
            assert result.result["content"] == "cached answer"
            assert result.result["cached"] is True

    def test_calls_llm_on_cache_miss(self):
        """On a cache miss the task calls generate_llm_response and caches the result."""
        with (
            patch("chatopsllm_api.worker.tasks._semantic_cache.get", return_value=None),
            patch("chatopsllm_api.worker.tasks._semantic_cache.set") as mock_set,
            patch(
                "chatopsllm_api.worker.tasks.asyncio.get_event_loop"
            ) as mock_loop,
        ):
            mock_result = MagicMock()
            mock_result.run_until_complete.return_value = "llm response"
            mock_loop.return_value = mock_result

            from chatopsllm_api.worker.tasks import generate_chat_response_task

            result = generate_chat_response_task.apply(
                kwargs={"prompt": "hi", "model": "test-model"}
            )
            assert result.result["content"] == "llm response"
            assert result.result["cached"] is False
            mock_set.assert_called_once_with("hi", "llm response")
