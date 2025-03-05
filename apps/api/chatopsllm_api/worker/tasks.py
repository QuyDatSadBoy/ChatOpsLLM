"""
Celery tasks for asynchronous LLM request processing.

The FastAPI service enqueues a ``generate_chat_response_task`` message to
RabbitMQ. A Celery worker picks it up, calls LiteLLM, and stores the result
in Redis so the caller can poll or stream it.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import asyncio
import json
import os
from typing import Optional

from chatopsllm_api import logger
from chatopsllm_api.cache.semantic_cache import SemanticCache
from chatopsllm_api.worker.celery_app import celery_app

_semantic_cache = SemanticCache()


@celery_app.task(
    bind=True,
    name="chatopsllm.generate_chat_response",
    max_retries=3,
    default_retry_delay=5,
)
def generate_chat_response_task(
    self,
    prompt: str,
    model: str = "gemini-flash",
    system_prompt: str = "",
    history: Optional[list] = None,
    prompt_type: Optional[str] = None,
) -> dict:
    """
    Async-safe Celery task that calls the LiteLLM proxy and returns the
    completed response text.

    The task checks the semantic cache first; on a miss it delegates to the
    LiteLLM client, caches the result, and returns it.

    Returns
    -------
    dict with keys:
        - ``content``: the generated text
        - ``model``: model name used
        - ``cached``: True if served from semantic cache
    """
    history = history or []

    cached = _semantic_cache.get(prompt)
    if cached:
        logger.info(f"[Task] Cache hit for task_id={self.request.id}")
        return {"content": cached, "model": model, "cached": True}

    try:
        from chatopsllm_api.llms.litellm import generate_llm_response

        result = asyncio.get_event_loop().run_until_complete(
            generate_llm_response(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                history=history,
                stream=False,
                json_mode=False,
            )
        )
        content = result if isinstance(result, str) else json.dumps(result)
        _semantic_cache.set(prompt, content)
        return {"content": content, "model": model, "cached": False}

    except Exception as exc:
        logger.error(f"[Task] Error task_id={self.request.id}: {exc}")
        raise self.retry(exc=exc)
