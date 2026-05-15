"""End-to-end scenario to validate meeting copilot behavior for a critical sentence."""
from orchestrator import Orchestrator


def test_meeting_copilot_detects_decision_and_legal_risk():
    orch = Orchestrator()
    sentence = "We need to decide today because legal identified compliance risks."
    result = orch.process(sentence)

    # Transcription -> summary produced
    assert isinstance(result.get("summary"), str)
    assert result.get("summary")

    # Alert detection: should include either a decision or risk label
    labels = [a.get("label", "") for a in result.get("alerts", [])]
    assert any(l in labels for l in ("Key Decision Detected", "Risk Signal Identified", "Time Pressure Detected")), f"Unexpected alerts: {labels}"

    # Action recommendations should be generated
    actions = result.get("actions", [])
    assert isinstance(actions, list)
    assert len(actions) > 0

    # Ensure decision-support style output (not only raw transcript)
    assert any("review" in a.lower() or "assign" in a.lower() or "risk" in a.lower() for a in actions)
