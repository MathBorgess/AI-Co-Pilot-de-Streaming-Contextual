"""Unit tests for agents (with mocked LLM)."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["MOCK_MODE"] = "true"

from agents.summarizer import SummarizerAgent
from agents.question_generator import QuestionGeneratorAgent
from agents.insight_generator import InsightGeneratorAgent


class TestSummarizerAgent:
    def test_initial_state(self):
        agent = SummarizerAgent()
        assert agent.current_summary == ""
        assert len(agent.accumulated_chunks) == 0

    def test_process_single_chunk(self):
        agent = SummarizerAgent()
        summary = agent.process("AI is transforming technology.")
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_process_accumulates_chunks(self):
        agent = SummarizerAgent()
        agent.process("First chunk about AI.")
        agent.process("Second chunk about streaming.")
        assert len(agent.accumulated_chunks) == 2

    def test_summary_updates_with_each_chunk(self):
        agent = SummarizerAgent()
        s1 = agent.process("Machine learning is powerful.")
        s2 = agent.process("Streaming enables real-time processing.")
        assert isinstance(s1, str)
        assert isinstance(s2, str)

    def test_reset_clears_state(self):
        agent = SummarizerAgent()
        agent.process("Some content.")
        agent.reset()
        assert agent.current_summary == ""
        assert len(agent.accumulated_chunks) == 0

    def test_process_with_context(self):
        agent = SummarizerAgent()
        context = ["Previous context about AI systems."]
        summary = agent.process("New information about agents.", context=context)
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestQuestionGeneratorAgent:
    def test_initial_state(self):
        agent = QuestionGeneratorAgent()
        assert len(agent.all_questions) == 0

    def test_generates_questions(self):
        agent = QuestionGeneratorAgent()
        questions = agent.process("AI streaming systems process data in real-time.")
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_questions_start_with_question_mark(self):
        agent = QuestionGeneratorAgent()
        questions = agent.process("Machine learning models transform data.")
        for q in questions:
            assert q.startswith("?"), f"Question should start with '?': {q}"

    def test_accumulates_questions(self):
        agent = QuestionGeneratorAgent()
        q1 = agent.process("First chunk.")
        q2 = agent.process("Second chunk.")
        assert len(q2) >= len(q1)

    def test_limits_questions_to_five(self):
        agent = QuestionGeneratorAgent()
        for i in range(10):
            agent.process(f"Chunk number {i} about AI and streaming.")
        assert len(agent.all_questions) <= 5

    def test_reset_clears_questions(self):
        agent = QuestionGeneratorAgent()
        agent.process("Some chunk.")
        agent.reset()
        assert len(agent.all_questions) == 0

    def test_process_with_context(self):
        agent = QuestionGeneratorAgent()
        context = ["Previous information about RAG systems."]
        questions = agent.process("Vector databases store embeddings.", context=context)
        assert isinstance(questions, list)


class TestInsightGeneratorAgent:
    def test_initial_state(self):
        agent = InsightGeneratorAgent()
        assert len(agent.all_insights) == 0

    def test_generates_insights(self):
        agent = InsightGeneratorAgent()
        insights = agent.process("RAG combines retrieval with generation.")
        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_insights_start_with_arrow(self):
        agent = InsightGeneratorAgent()
        insights = agent.process("Event-driven architectures scale well.")
        for insight in insights:
            assert insight.startswith("→"), f"Insight should start with '→': {insight}"

    def test_accumulates_insights(self):
        agent = InsightGeneratorAgent()
        i1 = agent.process("First insight chunk.")
        i2 = agent.process("Second insight chunk.")
        assert len(i2) >= len(i1)

    def test_limits_insights(self):
        agent = InsightGeneratorAgent()
        for i in range(10):
            agent.process(f"Chunk {i} about AI streaming and vector databases.")
        assert len(agent.all_insights) <= 6

    def test_reset_clears_insights(self):
        agent = InsightGeneratorAgent()
        agent.process("Some content.")
        agent.reset()
        assert len(agent.all_insights) == 0

    def test_process_with_context(self):
        agent = InsightGeneratorAgent()
        context = ["Context about multi-agent systems."]
        insights = agent.process("Agents coordinate to solve problems.", context=context)
        assert isinstance(insights, list)
