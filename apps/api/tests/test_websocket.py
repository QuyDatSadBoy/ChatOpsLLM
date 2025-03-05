"""
Tests for WebSocket chat endpoint.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from chatopsllm_api.main import app


class TestWebSocketChat:
    def test_ws_chat_done_signal_sent(self):
        """A complete round-trip over the WebSocket should end with [DONE]."""
        with (
            patch("chatopsllm_api.websocket.ws_handler._cache.get", return_value=None),
            patch("chatopsllm_api.websocket.ws_handler._cache.set"),
            patch(
                "chatopsllm_api.websocket.ws_handler._handler.handle_conversation",
                new_callable=AsyncMock,
            ) as mock_handle,
        ):
            # Simulate a streaming response
            async def _fake_body():
                for token in [b"Hello", b" world"]:
                    yield token

            mock_response = MagicMock()
            mock_response.body_iterator = _fake_body()
            mock_handle.return_value = mock_response

            client = TestClient(app)
            with client.websocket_connect("/ws/chat") as ws:
                ws.send_text(
                    json.dumps(
                        {
                            "latest_prompt": "hi",
                            "message": "",
                            "history": [],
                            "model": "gemini-flash",
                        }
                    )
                )
                tokens = []
                while True:
                    data = ws.receive_text()
                    if data == "[DONE]":
                        break
                    tokens.append(data)

            assert "".join(tokens) == "Hello world"

    def test_ws_chat_serves_from_cache(self):
        """If cache hits, the response is served immediately without calling the LLM."""
        cached = "I am the cached answer"

        with (
            patch("chatopsllm_api.websocket.ws_handler._cache.get", return_value=cached),
            patch(
                "chatopsllm_api.websocket.ws_handler._handler.handle_conversation"
            ) as mock_handle,
        ):
            client = TestClient(app)
            with client.websocket_connect("/ws/chat") as ws:
                ws.send_text(json.dumps({"latest_prompt": "cached?", "message": [], "history": []}))
                resp = ws.receive_text()
                done = ws.receive_text()

            assert resp == cached
            assert done == "[DONE]"
            mock_handle.assert_not_called()

    def test_ws_invalid_json_returns_error(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_text("not valid json {{{")
            err = ws.receive_text()
            assert "invalid JSON" in json.loads(err).get("error", "")
