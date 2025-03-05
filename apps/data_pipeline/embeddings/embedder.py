"""
Embedding helper for the data pipeline (sync, CPU-friendly).

Calls the LiteLLM proxy (or a local sentence-transformers model) to produce
dense embeddings for a batch of text chunks.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import os

import openai

_BASE_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
_API_KEY = os.getenv("LITELLM_API_KEY", "anything")
_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Return one embedding vector per chunk.

    Uses the OpenAI-compatible embeddings endpoint exposed by LiteLLM.
    """
    client = openai.OpenAI(api_key=_API_KEY, base_url=_BASE_URL)
    response = client.embeddings.create(model=_MODEL, input=chunks)
    return [item.embedding for item in response.data]
