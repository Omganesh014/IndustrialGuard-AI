"""
tests/rag/test_rag.py

Tests for RAG retrieval and document chunking logic.
"""

import pytest
from rag.retrieval.retriever import retrieve
from rag.ingestion.ingest import chunk_text, clean_text, detect_tier


class TestRagIngestion:
    def test_clean_text(self):
        dirty = "  Header \r\n\n\n\n Paragraph   with    spaces.  \x00"
        cleaned = clean_text(dirty)
        assert "\r" not in cleaned
        assert "\x00" not in cleaned
        assert "with spaces." in cleaned

    def test_chunk_text(self):
        text = "Paragraph 1 is short.\n\nParagraph 2 is also short."
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) >= 1
        assert "Paragraph 1" in chunks[0]

    def test_detect_tier(self):
        assert detect_tier("iso_13374_condition_monitoring.md") == 1
        assert detect_tier("tool_wear_thermal_compensation_guide.md") == 2
        assert detect_tier("demo_operating_procedures.md") == 3


class TestRagRetrieval:
    def test_retrieve_returns_relevant_passages(self):
        results = retrieve("tool wear failure cutting torque", top_k=2)
        assert len(results) > 0
        assert "content" in results[0]
        assert "source" in results[0]
        assert "tier" in results[0]

    def test_empty_query_returns_empty_list(self):
        assert retrieve("") == []
        assert retrieve("   ") == []
