"""
WebSocket handler for real-time chat streaming.

The frontend (Next.js) connects to ``/ws/chat`` via a persistent WebSocket.
Each incoming JSON message is processed by the ConversationHandler and the
LLM token stream is forwarded back to the client as it arrives.

Message format (client → server):
    {
        "message": [...],          // full chat history
        "latest_prompt": "...",
        "prompt_type": "enhance_prompt",
        "model": "gemini-flash"
    }

Message format (server → client):
    "token"   – a single streamed LLM token
    "[DONE]"  – stream complete marker

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import json
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from chatopsllm_api import logger
from chatopsllm_api.cache.semantic_cache import SemanticCache
from chatopsllm_api.chat_completion.conversation_handler import ConversationHandler
from chatopsllm_api.chat_completion.prompt_enhancer import DefaultPromptEnhancer
from chatopsllm_api.schemas.prompt_schema import ConversationIn

_cache = SemanticCache()
_handler = ConversationHandler(
    prompt_enhancer=DefaultPromptEnhancer(),
    model="gemini-flash",
)


async def handle_ws_chat(websocket: WebSocket) -> None:
    """
    Accept and drive a chat WebSocket connection until the client disconnects.
    """
    await websocket.accept()
    logger.info(f"[WS] Client connected: {websocket.client}")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "invalid JSON"}))
                continue

            prompt: str = payload.get("latest_prompt", "")
            model: str = payload.get("model", "gemini-flash")

            # Check semantic cache first
            cached_response: Optional[str] = _cache.get(prompt)
            if cached_response:
                logger.info("[WS] Serving from semantic cache")
                await websocket.send_text(cached_response)
                await websocket.send_text("[DONE]")
                continue

            data = ConversationIn(
                message=payload.get("message", "") if isinstance(payload.get("message"), str) else "",
                latest_prompt=prompt,
                prompt_type=payload.get("prompt_type", "enhance_prompt"),
                history=payload.get("history", []),
            )

            collected_tokens: list[str] = []
            try:
                streaming_response = await _handler.handle_conversation(data)
                async for chunk in streaming_response.body_iterator:
                    token = chunk.decode() if isinstance(chunk, bytes) else chunk
                    collected_tokens.append(token)
                    await websocket.send_text(token)
            except Exception as exc:
                logger.error(f"[WS] LLM error: {exc}")
                await websocket.send_text(json.dumps({"error": str(exc)}))
            else:
                full_response = "".join(collected_tokens)
                _cache.set(prompt, full_response)
                await websocket.send_text("[DONE]")

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: {websocket.client}")
    except Exception as exc:
        logger.error(f"[WS] Unexpected error: {exc}")
        await websocket.close(code=1011)
