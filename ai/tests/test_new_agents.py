"""Tests for AlertAgent, DirectionAgent, and system latency with new agents."""
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["MOCK_MODE"] = "true"

from agents.alert_agent import AlertAgent
from agents.direction_agent import DirectionAgent
from orchestrator import Orchestrator


class TestAlertAgent:
    def test_initial_state(self):
        agent = AlertAgent()
        assert len(agent.alert_history) == 0

    def test_fires_on_decision_keyword(self):
        agent = AlertAgent()
        history = agent.process("We need to decide whether to build or buy the solution.")
        assert len(history) == 1
        assert history[0]["label"] == "Key Decision Point"
        assert history[0]["emoji"] == "⚠️"

    def test_fires_on_deadline_keyword(self):
        agent = AlertAgent()
        history = agent.process("The deadline is next quarter and we cannot slip further.")
        assert len(history) == 1
        assert history[0]["label"] == "Time Pressure Detected"
        assert history[0]["emoji"] == "🔥"

    def test_fires_on_conflict_keyword(self):
        agent = AlertAgent()
        history = agent.process("The team is split on this approach and tension is rising.")
        assert len(history) == 1
        assert history[0]["label"] == "Team Conflict Detected"

    def test_fires_on_risk_keyword(self):
        agent = AlertAgent()
        history = agent.process("Legal has flagged serious compliance concerns with the vendor.")
        assert len(history) == 1
        assert history[0]["label"] == "Risk Signal Identified"

    def test_fires_on_competitor_keyword(self):
        agent = AlertAgent()
        history = agent.process("Our competitor is already gaining traction with enterprise clients.")
        assert len(history) == 1
        assert history[0]["label"] == "Competitive Signal"

    def test_fires_on_critical_keyword(self):
        agent = AlertAgent()
        history = agent.process("This is a critical blocker for the entire roadmap.")
        assert len(history) == 1
        assert history[0]["label"] == "Critical Issue Flagged"

    def test_fires_on_financial_keyword(self):
        agent = AlertAgent()
        history = agent.process("The budget for this initiative needs board approval first.")
        assert len(history) == 1
        assert history[0]["label"] == "Financial Implication"

    def test_no_alert_for_neutral_content(self):
        agent = AlertAgent()
        history = agent.process("The meeting started at nine and the agenda was shared.")
        assert len(history) == 0

    def test_alert_detail_contains_chunk_text(self):
        agent = AlertAgent()
        chunk = "We need to decide on the architecture by Friday."
        history = agent.process(chunk)
        assert len(history) == 1
        assert history[0]["detail"].startswith("We need to decide")

    def test_accumulates_alerts_across_chunks(self):
        agent = AlertAgent()
        agent.process("We need to decide on the build vs buy question.")
        agent.process("The deadline is next quarter and we cannot slip.")
        assert len(agent.alert_history) == 2

    def test_caps_history_at_eight(self):
        agent = AlertAgent()
        for _ in range(10):
            agent.alert_history.append({"emoji": "⚠️", "label": "Key Decision Point", "detail": "x"})
        # Process one more
        result = agent.process("We need to decide on the vendor contract.")
        assert len(result) <= 8

    def test_one_alert_per_chunk(self):
        """Even if multiple patterns match, only one alert fires per chunk."""
        agent = AlertAgent()
        # 'critical' + 'decision' both match — only first-priority fires
        history = agent.process("This is a critical blocker and we need to decide immediately.")
        assert len(history) == 1

    def test_reset_clears_history(self):
        agent = AlertAgent()
        agent.process("We need to decide now.")
        agent.reset()
        assert len(agent.alert_history) == 0

    def test_alert_has_required_fields(self):
        agent = AlertAgent()
        history = agent.process("We need to decide on this today.")
        assert "emoji" in history[0]
        assert "label" in history[0]
        assert "detail" in history[0]

    def test_detail_truncated_to_120_chars(self):
        agent = AlertAgent()
        long_chunk = "We need to decide " + "x" * 200
        history = agent.process(long_chunk)
        assert len(history[0]["detail"]) <= 120


class TestDirectionAgent:
    def test_initial_state(self):
        agent = DirectionAgent()
        assert len(agent.current_directions) == 0

    def test_generates_directions(self):
        agent = DirectionAgent()
        directions = agent.process("We need to decide on the architecture today.")
        assert isinstance(directions, list)
        assert len(directions) > 0

    def test_directions_start_with_arrow(self):
        agent = DirectionAgent()
        directions = agent.process("We need to decide on the launch date.")
        for d in directions:
            assert d.startswith("→"), f"Direction should start with '→': {d}"

    def test_decision_context_gives_decision_directions(self):
        agent = DirectionAgent()
        directions = agent.process("We need to decide whether to build or buy the solution.")
        # Should suggest assignment of a DRI or setting a deadline
        combined = " ".join(directions).lower()
        assert any(word in combined for word in ["assign", "dri", "deadline", "document"])

    def test_risk_context_gives_risk_directions(self):
        agent = DirectionAgent()
        directions = agent.process("Legal has flagged compliance concerns with the vendor.")
        combined = " ".join(directions).lower()
        assert any(word in combined for word in ["risk", "stakeholder", "mitigation", "contingency"])

    def test_deadline_context_gives_deadline_directions(self):
        agent = DirectionAgent()
        directions = agent.process("The deadline is next quarter and we cannot slip.")
        combined = " ".join(directions).lower()
        assert any(word in combined for word in ["dependencies", "milestone", "scope", "deadline"])

    def test_conflict_context_gives_conflict_directions(self):
        agent = DirectionAgent()
        directions = agent.process("The team is split and tension is high — both sides are pushing back hard.")
        combined = " ".join(directions).lower()
        assert any(word in combined for word in ["document", "perspectives", "escalate", "spike"])

    def test_returns_directions_for_neutral_content(self):
        agent = DirectionAgent()
        directions = agent.process("The meeting started and everyone introduced themselves.")
        assert isinstance(directions, list)
        assert len(directions) > 0  # always returns something (default category)

    def test_accepts_recent_alerts_parameter(self):
        agent = DirectionAgent()
        alerts = [{"emoji": "⚠️", "label": "Key Decision Point", "detail": "..."}]
        directions = agent.process("We need to decide on the vendor.", recent_alerts=alerts)
        assert isinstance(directions, list)

    def test_reset_clears_directions(self):
        agent = DirectionAgent()
        agent.process("We need to decide now.")
        agent.reset()
        assert len(agent.current_directions) == 0

    def test_max_three_directions(self):
        agent = DirectionAgent()
        directions = agent.process("We need to decide on the build vs buy question.")
        assert len(directions) <= 3


class TestNewAgentsLatency:
    def test_alert_agent_is_fast(self):
        """AlertAgent uses pattern matching — should be near-instant."""
        agent = AlertAgent()
        start = time.time()
        for _ in range(50):
            agent.process("We need to decide on the architecture today.")
        elapsed = time.time() - start
        assert elapsed < 1.0, f"50 AlertAgent calls took {elapsed:.3f}s, expected < 1s"

    def test_full_pipeline_with_new_agents_under_3s(self):
        """Full orchestrator pipeline with 5 chunks must complete under 3s each."""
        orch = Orchestrator()
        demo_chunks = [
            "We are here to make a final decision on the AI copilot launch strategy.",
            "The deadline is end of next quarter and engineering says we cannot slip further.",
            "The team is split: some want to ship now, others are concerned about technical debt.",
            "Legal has flagged serious concerns about data privacy compliance with the vendor.",
            "The recommendation is to ship a limited version now and iterate toward the full solution.",
        ]
        for i, chunk in enumerate(demo_chunks):
            start = time.time()
            result = orch.process(chunk, chunk_index=i + 1, total_chunks=len(demo_chunks))
            elapsed = time.time() - start
            assert elapsed < 3.0, f"Chunk {i+1} took {elapsed:.3f}s, expected < 3s"
            assert "alerts" in result
            assert "directions" in result

    def test_alerts_fire_on_demo_scenario(self):
        """All key moments in the demo script should trigger at least 5 alerts."""
        orch = Orchestrator()
        demo_chunks = [
            "We are here to make a final decision on the AI copilot launch strategy.",
            "The deadline is end of next quarter and engineering says we cannot slip further.",
            "The team is split: some want to ship now, others are concerned about technical debt.",
            "Legal has flagged serious concerns about data privacy compliance with the vendor.",
            "Our competitor launched a similar feature last week and is gaining enterprise traction.",
            "If we delay, we risk losing three key enterprise accounts evaluating our platform.",
            "The engineering lead confirmed that technical debt is a critical blocker.",
            "The recommendation is to ship a limited version now and iterate toward the full solution.",
        ]
        for chunk in demo_chunks:
            orch.process(chunk)

        total_alerts = len(orch.alert_agent.alert_history)
        assert total_alerts >= 5, f"Expected ≥5 alerts for demo scenario, got {total_alerts}"

    def test_orchestrator_result_has_all_fields(self):
        orch = Orchestrator()
        result = orch.process("We need to decide on the build vs buy strategy today.", chunk_index=1, total_chunks=5)
        required = {"summary", "questions", "insights", "alerts", "directions",
                    "chunkIndex", "totalChunks", "processingTimeMs", "totalChunksProcessed"}
        for field in required:
            assert field in result, f"Missing field: {field}"

    def test_orchestrator_reset_clears_new_agents(self):
        orch = Orchestrator()
        orch.process("We need to decide on the build vs buy strategy.")
        orch.reset()
        assert len(orch.alert_agent.alert_history) == 0
        assert len(orch.direction_agent.current_directions) == 0
