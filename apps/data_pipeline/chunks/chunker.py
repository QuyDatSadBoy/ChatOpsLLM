"""
Document chunker – splits long text into overlapping windows.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

from __future__ import annotations

import re
from typing import Optional


def chunk_texts(
    text: str,
    source: str = "",
    chunk_size: int = 512,
    overlap: int = 64,
) -> tuple[list[str], list[dict]]:
    """
    Split *text* into overlapping chunks of *chunk_size* characters with
    *overlap* characters carried over to the next chunk.

    Returns
    -------
    chunks  : list of text strings
    metadata: list of dicts with keys ``text``, ``source``, ``chunk_index``
    """
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return [], []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    metadata = [
        {"text": c, "source": source, "chunk_index": i}
        for i, c in enumerate(chunks)
    ]
    return chunks, metadata
