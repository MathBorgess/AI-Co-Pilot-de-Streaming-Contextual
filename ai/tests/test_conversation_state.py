"""Long-form conversation state tests for semantic continuity."""
from orchestrator import Orchestrator


def test_conversation_state_persists_and_evolves_across_semantic_shifts():
    orch = Orchestrator()

    chunks = [
        "We're studying hypertrophy mechanics and neural activation during compound lifts.",
        "The discussion keeps returning to activation quality and whether isolation work changes recruitment.",
        "Can you teach this methodology in a simpler way for the class and explain the core concept?",
        "Now the architecture topic appears: we need to reason about latency, coupling, and service boundaries.",
        "The system design still has event consistency concerns, and the technical trade-off needs validation.",
        "Let's focus on the architecture choice and the smallest safe change before we commit to a direction.",
    ]

    results = []
    for index, chunk in enumerate(chunks, start=1):
        results.append(orch.process(chunk, chunk_index=index, total_chunks=len(chunks)))

    final_state = results[-1]["conversation_state"]

    assert orch.chunk_count == len(chunks)
    assert orch.rag.chunk_count() == len(chunks)

    # The early sports science context should persist long enough to influence the state.
    assert any("activation" in topic or "hypertrophy" in topic for topic in final_state.get("emergingTopics", []))

    # Later chunks should move the stable domain toward software engineering.
    assert final_state.get("stableDomain") == "software engineering"
    assert final_state.get("currentMode") in {"technical discussion", "analysis", "decision making"}

    # A continuous cognitive trail should exist.
    assert len(final_state.get("confidenceTrend", [])) >= len(chunks) - 1
    assert len(final_state.get("understandingTimeline", [])) > 0
    assert len(final_state.get("openThreads", [])) > 0
    assert len(final_state.get("unresolvedQuestions", [])) > 0

    transitions = final_state.get("semanticTransitions", [])
    assert any("shifted" in item.lower() or "deepened" in item.lower() for item in transitions)
    assert any("teaching" in item.lower() for item in transitions)
    assert any("software engineering" in item.lower() for item in transitions)

    # Actions should reflect the final technical context rather than a generic corporate template.
    final_actions = results[-1].get("actions", [])
    combined = " ".join(final_actions).lower()
    assert any(term in combined for term in ["architecture", "constraint", "validation", "technical"])

    # Alerts should preserve memory and can become domain-specific.
    alert_labels = [item["label"] for item in orch.alert_agent.alert_history]
    assert any("uncertainty" in label.lower() or "choice" in label.lower() for label in alert_labels)
