"""Direction Agent - suggests concrete next steps based on the current context."""
from typing import List, Dict
from .base import BaseAgent

_DIRECTION_MAP: Dict[str, List[str]] = {
    "decision": [
        "Assign a DRI (Directly Responsible Individual) before this session ends.",
        "Set a deadline to revisit if no consensus is reached today.",
        "Document the decision criteria in writing for async review.",
    ],
    "risk": [
        "Request a dedicated risk assessment before proceeding.",
        "Loop in the relevant stakeholders to mitigate the identified concern.",
        "Create a contingency plan for the flagged issue.",
    ],
    "deadline": [
        "Verify all dependencies are unblocked before committing to the timeline.",
        "Break down remaining work into weekly milestones.",
        "Identify the minimum viable scope to hit the deadline.",
    ],
    "conflict": [
        "Document both perspectives and share async before the next decision point.",
        "Run a time-boxed spike to gather data and resolve the disagreement.",
        "Escalate to leadership if alignment cannot be reached in this session.",
    ],
    "competitor": [
        "Schedule a competitive analysis review within the next sprint.",
        "Define the differentiation angle against the competitor's move.",
    ],
    "financial": [
        "Request a cost-benefit analysis before final approval.",
        "Identify the ROI threshold that would justify this investment.",
    ],
    "default": [
        "Capture action items and owners before this session closes.",
        "Schedule a follow-up to validate the assumptions raised here.",
        "Send a written summary of key decisions to the wider team.",
    ],
}


def _detect_category(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in ["decide", "decision", "final call", "commit to", "recommendation is", "we need to decide"]):
        return "decision"
    if any(kw in t for kw in ["risk", "legal", "compliance", "flagged", "blocker"]):
        return "risk"
    if any(kw in t for kw in ["deadline", "cannot slip", "ship", "launch", "quarter"]):
        return "deadline"
    if any(kw in t for kw in ["split", "conflict", "disagree", "tension", "push back"]):
        return "conflict"
    if any(kw in t for kw in ["competitor", "competition", "market", "losing", "traction"]):
        return "competitor"
    if any(kw in t for kw in ["budget", "cost", "invest", "revenue", "financial", "roi"]):
        return "financial"
    return "default"


class DirectionAgent(BaseAgent):
    """Agent that suggests next steps and recommended actions."""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.current_directions: List[str] = []

    def process(self, chunk: str, recent_alerts: List[dict] = None) -> List[str]:
        """Generate recommended actions based on the chunk and recent alerts."""
        alert_labels = [a["label"] for a in (recent_alerts or [])]
        prompt = (
            f"You are a strategic direction agent in a meeting copilot.\n"
            f"Based on this content, suggest 2-3 concrete next steps.\n\n"
            f"Content: {chunk}\n"
            f"Recent alerts: {alert_labels or 'none'}\n\n"
            f"Format: Return exactly 2-3 action items, one per line, starting with '→'.\n"
            f"Actions:"
        )
        response = self._call_llm(prompt)
        directions = [line.strip() for line in response.split("\n") if line.strip().startswith("→")]
        if directions:
            self.current_directions = directions[:3]
        return self.current_directions

    def _mock_response(self, prompt: str) -> str:
        """Keyword-driven mock directions."""
        category = _detect_category(prompt)
        templates = _DIRECTION_MAP[category]
        return "\n".join(f"→ {t}" for t in templates[:2])

    def reset(self):
        """Reset agent state."""
        self.current_directions.clear()
