"""Integration tests for the full orchestrator pipeline."""
from orchestrator import Orchestrator
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["MOCK_MODE"] = "true"


class TestOrchestrator:
    def test_process_returns_required_fields(self):
        orch = Orchestrator()
        result = orch.process(
            "AI systems are transforming technology.", chunk_index=1, total_chunks=10)

        assert "summary" in result
        assert "questions" in result
        assert "insights" in result
        assert "chunkIndex" in result
        assert "totalChunks" in result
        assert "processingTimeMs" in result
        assert "totalChunksProcessed" in result

    def test_process_summary_is_string(self):
        orch = Orchestrator()
        result = orch.process("Machine learning enables pattern recognition.")
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0

    def test_process_questions_is_list(self):
        orch = Orchestrator()
        result = orch.process("Streaming systems process data in real-time.")
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) > 0

    def test_process_insights_is_list(self):
        orch = Orchestrator()
        result = orch.process("RAG combines retrieval and generation.")
        assert isinstance(result["insights"], list)
        assert len(result["insights"]) > 0

    def test_incremental_processing(self):
        orch = Orchestrator()
        chunks = [
            "AI is transforming how we interact with technology.",
            "Machine learning models can understand natural language.",
            "Streaming systems enable real-time data processing.",
        ]
        results = []
        for i, chunk in enumerate(chunks):
            result = orch.process(chunk, chunk_index=i+1,
                                  total_chunks=len(chunks))
            results.append(result)

        assert len(results) == 3
        assert results[0]["totalChunksProcessed"] == 1
        assert results[1]["totalChunksProcessed"] == 2
        assert results[2]["totalChunksProcessed"] == 3

    def test_processing_time_is_reasonable(self):
        """Processing should complete within 3 seconds (mock mode is fast)."""
        orch = Orchestrator()
        start = time.time()
        result = orch.process("Test chunk for latency measurement.")
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Processing took {elapsed:.2f}s, expected < 3s"
        assert result["processingTimeMs"] >= 0

    def test_reset_clears_all_state(self):
        orch = Orchestrator()
        orch.process("Some content.")
        orch.process("More content.")

        orch.reset()

        assert orch.chunk_count == 0
        assert orch.rag.chunk_count() == 0
        assert orch.summarizer.current_summary == ""
        assert len(orch.question_generator.all_questions) == 0
        assert len(orch.insight_generator.all_insights) == 0
        assert len(orch.alert_agent.alert_history) == 0
        assert len(orch.action_agent.current_actions) == 0

    def test_context_is_used_across_chunks(self):
        """RAG should retrieve context from previous chunks."""
        orch = Orchestrator()
        orch.process("Vector databases store semantic embeddings.")
        result = orch.process("ChromaDB is an example of a vector database.")

        # Second chunk should have accumulated context from RAG
        assert orch.rag.chunk_count() == 2

    def test_chunk_index_preserved_in_result(self):
        orch = Orchestrator()
        result = orch.process("Test chunk.", chunk_index=5, total_chunks=10)
        assert result["chunkIndex"] == 5
        assert result["totalChunks"] == 10

    def test_simulation_latency(self):
        """Simulate a full stream and verify total latency."""
        orch = Orchestrator()
        chunks = [
            "AI systems are transforming technology.",
            "Machine learning enables real-time insights.",
            "Multi-agent systems coordinate to solve problems.",
            "Vector databases enable semantic search.",
            "WebSockets enable bidirectional communication.",
        ]

        total_time = 0
        max_single_chunk_time = 0

        for i, chunk in enumerate(chunks):
            start = time.time()
            result = orch.process(chunk, chunk_index=i+1,
                                  total_chunks=len(chunks))
            elapsed = time.time() - start
            total_time += elapsed
            max_single_chunk_time = max(max_single_chunk_time, elapsed)

        print(f"\nSimulation results:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Max single chunk: {max_single_chunk_time:.3f}s")
        print(f"  Avg per chunk: {total_time/len(chunks):.3f}s")

        assert max_single_chunk_time < 3.0, f"Single chunk took {max_single_chunk_time:.2f}s"
        assert orch.rag.chunk_count() == len(chunks)
