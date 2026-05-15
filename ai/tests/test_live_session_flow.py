"""Simulated live-session test for continuity and topic-shift behavior."""
from orchestrator import Orchestrator


def test_live_session_continuity_and_topic_shift():
    orch = Orchestrator()

    # Simulates 2-3 minutes of evolving conversation in chunks.
    session_chunks = [
        "We need to decide today who owns launch readiness.",
        "Legal identified compliance risks and we cannot approve without clear accountability.",
        "Deadline is in two weeks and we cannot delay again.",
        "Switching topic: our competitor launched a similar feature and is gaining traction.",
        "Given this, we should align on a go/no-go owner before the next sync.",
    ]

    results = []
    for idx, chunk in enumerate(session_chunks, start=1):
        results.append(orch.process(chunk, chunk_index=idx, total_chunks=len(session_chunks)))

    # The system should keep accumulating context, not reset per chunk.
    assert orch.chunk_count == len(session_chunks)
    assert orch.rag.chunk_count() == len(session_chunks)

    all_alert_labels = [a["label"] for a in orch.alert_agent.alert_history]

    # Detects key moments across changing topics.
    assert "Key Decision Detected" in all_alert_labels
    assert "Risk Signal Identified" in all_alert_labels
    assert any(label in all_alert_labels for label in ["Time Pressure Detected", "Competitive Signal"])

    # Action suggestions remain available and coherent through the flow.
    final_actions = results[-1].get("actions", [])
    assert len(final_actions) > 0
    assert any(
        key in " ".join(final_actions).lower()
        for key in ["owner", "compliance", "go/no-go", "decision"]
    )
