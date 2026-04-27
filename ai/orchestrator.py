"""Orchestrator - coordinates RAG + Agents pipeline."""
import os
import time
from typing import Dict, Any, Optional

from rag.engine import RAGEngine
from agents.summarizer import SummarizerAgent
from agents.question_generator import QuestionGeneratorAgent
from agents.insight_generator import InsightGeneratorAgent


def create_llm():
    """Create LLM instance if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
    
    if mock_mode or not api_key or api_key == "your_key_here":
        print("[Orchestrator] Running in MOCK mode (no LLM)")
        return None
    
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=api_key)
        print("[Orchestrator] OpenAI LLM initialized")
        return llm
    except Exception as e:
        print(f"[Orchestrator] LLM init error: {e}, using mock mode")
        return None


class Orchestrator:
    """Coordinates the RAG + Agents pipeline."""

    def __init__(self):
        self.rag = RAGEngine()
        llm = create_llm()
        self.summarizer = SummarizerAgent(llm=llm)
        self.question_generator = QuestionGeneratorAgent(llm=llm)
        self.insight_generator = InsightGeneratorAgent(llm=llm)
        self.chunk_count = 0

    def process(self, chunk: str, chunk_index: int = 0, total_chunks: int = 0) -> Dict[str, Any]:
        """
        Full pipeline: chunk → RAG storage → agent processing.
        
        Returns:
            dict with summary, questions, insights, and metadata
        """
        start_time = time.time()
        self.chunk_count += 1

        # Step 1: Store chunk in RAG
        chunk_id = self.rag.add_chunk(chunk, metadata={
            "index": chunk_index,
            "total": total_chunks,
        })

        # Step 2: Retrieve relevant context
        context = self.rag.retrieve(chunk, n_results=3)

        # Step 3: Run agents in sequence
        summary = self.summarizer.process(chunk, context)
        questions = self.question_generator.process(chunk, context)
        insights = self.insight_generator.process(chunk, context)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "summary": summary,
            "questions": questions,
            "insights": insights,
            "chunkIndex": chunk_index,
            "totalChunks": total_chunks,
            "chunkId": chunk_id,
            "processingTimeMs": elapsed_ms,
            "totalChunksProcessed": self.chunk_count,
        }

    def reset(self):
        """Reset all state."""
        self.rag.clear()
        self.summarizer.reset()
        self.question_generator.reset()
        self.insight_generator.reset()
        self.chunk_count = 0
