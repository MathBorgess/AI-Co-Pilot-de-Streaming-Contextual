"""Orchestrator - coordinates RAG + Agents pipeline."""
import os
import time
from typing import Dict, Any, Optional

from rag.engine import RAGEngine
from agents.summarizer import SummarizerAgent
from agents.question_generator import QuestionGeneratorAgent
from agents.insight_generator import InsightGeneratorAgent
from agents.alert_agent import AlertAgent
from agents.action_agent import ActionAgent
from agents.conversation_domain_agent import ConversationDomainAgent


def create_llm():
    """Create LLM instance if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"

    if mock_mode or not api_key or api_key == "your_key_here":
        print("[Orchestrator] Running in MOCK mode (no LLM)")
        return None

    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo",
                         temperature=0.7, api_key=api_key)
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
        self.alert_agent = AlertAgent(llm=llm)
        self.action_agent = ActionAgent(llm=llm)
        # conversation domain modeling agent — lightweight, incremental
        self.conversation_agent = ConversationDomainAgent(llm=llm)
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
        print(f"[RAG] Retrieved {len(context)} context items. Focus_terms={self.rag.get_focus_terms()}")

        # Step 3: Semantic conversation modeling -> domain-aware agents
        conversation_meta = self.conversation_agent.process(chunk, context)
        print(f"[CONV_AGENT] inferred={conversation_meta}")

        summary = self.summarizer.process(chunk, context, conversation=conversation_meta)
        print(f"[SUMMARIZER] summary_len={len(summary or '')}")
        questions = self.question_generator.process(chunk, context, conversation=conversation_meta)
        insights = self.insight_generator.process(chunk, context, conversation=conversation_meta)
        alerts = self.alert_agent.process(
            chunk,
            conversation=conversation_meta,
            conversation_state=conversation_meta.get("conversation_state"),
        )
        actions = self.action_agent.process(
            chunk,
            context=context,
            recent_alerts=alerts[-3:],
            conversation=conversation_meta,
            conversation_state=conversation_meta.get("conversation_state"),
        )
        print(f"[ACTION_AGENT] actions_generated={len(actions)}")
        focus_terms = self.rag.get_focus_terms()

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "summary": summary,
            "conversation": conversation_meta,
            "conversation_state": conversation_meta.get("conversation_state", {}),
            "questions": questions,
            "insights": insights,
            "alerts": alerts,
            "actions": actions,
            "directions": actions,
            "focusTerms": focus_terms,
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
        self.alert_agent.reset()
        self.action_agent.reset()
        self.conversation_agent.reset()
        self.chunk_count = 0
