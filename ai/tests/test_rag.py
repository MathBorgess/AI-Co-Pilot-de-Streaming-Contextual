"""Unit tests for RAG Engine."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["MOCK_MODE"] = "true"

from rag.engine import RAGEngine


class TestRAGEngine:
    def test_initialize(self):
        rag = RAGEngine()
        rag.initialize()
        assert rag._initialized

    def test_add_chunk_returns_id(self):
        rag = RAGEngine()
        chunk_id = rag.add_chunk("Test chunk about AI.")
        assert isinstance(chunk_id, str)
        assert len(chunk_id) > 0

    def test_chunk_count_increases(self):
        rag = RAGEngine()
        assert rag.chunk_count() == 0
        rag.add_chunk("First chunk.")
        assert rag.chunk_count() == 1
        rag.add_chunk("Second chunk.")
        assert rag.chunk_count() == 2

    def test_get_all_chunks(self):
        rag = RAGEngine()
        rag.add_chunk("Chunk one.")
        rag.add_chunk("Chunk two.")
        chunks = rag.get_all_chunks()
        assert len(chunks) == 2

    def test_retrieve_returns_list(self):
        rag = RAGEngine()
        rag.add_chunk("AI systems process data.")
        rag.add_chunk("Machine learning transforms input.")
        results = rag.retrieve("AI data processing")
        assert isinstance(results, list)

    def test_retrieve_returns_empty_when_no_data(self):
        rag = RAGEngine()
        results = rag.retrieve("anything")
        assert results == []

    def test_clear_resets_chunks(self):
        rag = RAGEngine()
        rag.add_chunk("Some chunk.")
        rag.clear()
        assert rag.chunk_count() == 0

    def test_add_chunk_with_metadata(self):
        rag = RAGEngine()
        chunk_id = rag.add_chunk("Test chunk.", metadata={"index": 1, "total": 10})
        assert isinstance(chunk_id, str)

    def test_retrieve_n_results(self):
        rag = RAGEngine()
        for i in range(5):
            rag.add_chunk(f"Chunk number {i} about AI systems and machine learning.")
        results = rag.retrieve("AI machine learning", n_results=2)
        assert len(results) <= 2

    def test_multiple_instances_are_independent(self):
        rag1 = RAGEngine(collection_name="test_col_1")
        rag2 = RAGEngine(collection_name="test_col_2")
        rag1.add_chunk("Chunk for rag1.")
        assert rag2.chunk_count() == 0
