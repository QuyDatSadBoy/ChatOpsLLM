"""
Embedding helper.

Wraps the LiteLLM proxy (or any OpenAI-compatible endpoint) to produce
text embeddings that are stored in Qdrant for RAG retrieval.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import os
from typing import Union

import openai

from chatopsllm_api import logger

_EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
_LITELLM_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
_LITELLM_KEY = os.getenv("LITELLM_API_KEY", "anything")


def _get_client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(api_key=_LITELLM_KEY, base_url=_LITELLM_URL)


async def embed_texts(texts: Union[str, list[str]]) -> list[list[float]]:
    """
    Return embeddings for *texts* using the configured embedding model.

    Parameters
    ----------
    texts:
        A single string or a list of strings to embed.

    Returns
    -------
    list of embedding vectors (one per input text).
    """
    if isinstance(texts, str):
        texts = [texts]

    client = _get_client()
    try:
        response = await client.embeddings.create(model=_EMBED_MODEL, input=texts)
        vectors = [item.embedding for item in response.data]
        logger.info(f"[Embeddings] Embedded {len(texts)} texts via '{_EMBED_MODEL}'")
        return vectors
    except Exception as exc:
        logger.error(f"[Embeddings] Failed to embed: {exc}")
        raise
