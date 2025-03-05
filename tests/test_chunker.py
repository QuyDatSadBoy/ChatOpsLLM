"""
Tests for the data pipeline chunker.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import sys
import os

# Add the data_pipeline root to path so we can import the local modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "data_pipeline"))

import pytest
from chunks.chunker import chunk_texts


class TestChunkTexts:
    def test_empty_string_returns_empty(self):
        chunks, meta = chunk_texts("")
        assert chunks == []
        assert meta == []

    def test_single_chunk_when_text_shorter_than_size(self):
        text = "short text"
        chunks, meta = chunk_texts(text, chunk_size=512)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_overlap_produces_correct_count(self):
        text = "a" * 100
        chunks, meta = chunk_texts(text, chunk_size=50, overlap=10)
        # Expected starts: 0, 40, 80 → 3 chunks
        assert len(chunks) == 3

    def test_metadata_contains_source_and_index(self):
        chunks, meta = chunk_texts("hello world test", source="doc.txt", chunk_size=8, overlap=0)
        for i, m in enumerate(meta):
            assert m["source"] == "doc.txt"
            assert m["chunk_index"] == i
            assert "text" in m

    def test_metadata_aligns_with_chunks(self):
        text = "x" * 200
        chunks, meta = chunk_texts(text, chunk_size=60, overlap=10)
        assert len(chunks) == len(meta)
        for chunk, m in zip(chunks, meta):
            assert m["text"] == chunk
