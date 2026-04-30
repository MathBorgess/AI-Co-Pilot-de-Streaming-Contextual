"""Alert Agent - detects key moments, decisions, and risks in the stream."""
from typing import List, Dict, Any
from .base import BaseAgent

# Priority-ordered patterns: first match wins per chunk
ALERT_PATTERNS = [
    {
        "keywords": ["critical", "urgent", "blocker", "showstopper", "cannot proceed"],
        "emoji": "🚨",
        "label": "Critical Issue Flagged",
    },
    {
        "keywords": ["decide", "decision", "final call", "vote", "commit to", "recommendation is", "we need to decide"],
        "emoji": "⚠️",
        "label": "Key Decision Point",
    },
    {
        "keywords": ["deadline", "cannot slip", "end of quarter", "ship by", "launch by", "release by"],
        "emoji": "🔥",
        "label": "Time Pressure Detected",
    },
    {
        "keywords": ["split", "disagree", "push back", "tension", "debate", "opposed", "worried"],
        "emoji": "⚡",
        "label": "Team Conflict Detected",
    },
    {
        "keywords": ["risk", "legal", "compliance", "flagged", "liability", "violation"],
        "emoji": "🛡️",
        "label": "Risk Signal Identified",
    },
    {
        "keywords": ["competitor", "competition", "market", "losing", "traction", "gaining ground"],
        "emoji": "📊",
        "label": "Competitive Signal",
    },
    {
        "keywords": ["budget", "cost", "invest", "spend", "revenue", "financial", "roi"],
        "emoji": "💰",
        "label": "Financial Implication",
    },
]


class AlertAgent(BaseAgent):
    """
    Agent that detects key moments and fires alerts.
    Operates via keyword pattern-matching — no LLM required.
    This makes it instant, reliable, and always suitable for live demos.
    """

    def __init__(self, llm=None):
        super().__init__(llm)
        self.alert_history: List[Dict[str, Any]] = []

    def process(self, chunk: str) -> List[Dict[str, Any]]:
        """
        Scan the chunk for alert patterns.
        Returns the full alert history (newest last), capped at 8 entries.
        """
        chunk_lower = chunk.lower()
        for pattern in ALERT_PATTERNS:
            if any(kw in chunk_lower for kw in pattern["keywords"]):
                alert: Dict[str, Any] = {
                    "emoji": pattern["emoji"],
                    "label": pattern["label"],
                    # Show first 120 chars so the UI has context
                    "detail": chunk[:120],
                }
                self.alert_history = (self.alert_history + [alert])[-8:]
                break  # one alert per chunk — highest-priority pattern wins

        return self.alert_history

    def _mock_response(self, prompt: str) -> str:
        # AlertAgent does not call the LLM; pattern matching is always used
        return ""

    def reset(self):
        """Reset alert history."""
        self.alert_history.clear()
