"""Alert Agent - detects key moments, decisions, and risks in the stream."""
from typing import List, Dict, Any
from .base import BaseAgent

# Priority-ordered patterns: first match wins per chunk
ALERT_PATTERNS = [
    {
        "keywords": ["critical", "urgent", "blocker", "showstopper", "cannot proceed", "critico", "critica", "bloqueador"],
        "emoji": "🚨",
        "label": "Critical Issue Flagged",
    },
    {
        "keywords": [
            "decide", "decision", "final call", "vote", "commit to", "recommendation is", "we need to decide",
            "decisao", "decidir", "decidimos", "vamos decidir", "voto", "go/no-go",
        ],
        "emoji": "⚠️",
        "label": "Key Decision Detected",
    },
    {
        "keywords": ["risk", "legal", "compliance", "flagged", "liability", "violation", "risco", "juridico", "conformidade"],
        "emoji": "🛡️",
        "label": "Risk Signal Identified",
    },
    {
        "keywords": ["deadline", "cannot slip", "end of quarter", "ship by", "launch by", "release by", "prazo", "nao podemos atrasar"],
        "emoji": "⏳",
        "label": "Time Pressure Detected",
    },
    {
        "keywords": ["split", "disagree", "push back", "tension", "debate", "opposed", "worried", "conflito", "discorda", "dividido"],
        "emoji": "⚡",
        "label": "Team Conflict Detected",
    },
    {
        "keywords": ["competitor", "competition", "market", "losing", "traction", "gaining ground", "concorrente", "competicao"],
        "emoji": "📊",
        "label": "Competitive Signal",
    },
    {
        "keywords": ["budget", "cost", "invest", "spend", "revenue", "financial", "roi", "orcamento", "custo", "receita"],
        "emoji": "💰",
        "label": "Financial Implication",
    },
    {
        "keywords": [
            "architecture", "strategy", "roadmap", "platform", "trade-off", "scope", "positioning",
            "arquitetura", "estrategia", "roteiro", "escopo", "proposta de valor",
        ],
        "emoji": "🔥",
        "label": "Critical Concept",
    },
    {
        "keywords": ["insight", "signal", "pattern", "learning", "evidence", "insight", "sinal", "padrao", "aprendizado"],
        "emoji": "📌",
        "label": "Important Insight",
    },
]

_DOMAIN_ALERT_MAP = {
    "sports": {
        "Key Decision Detected": "Training Method Decision Detected",
        "Critical Issue Flagged": "Training Problem Detected",
        "Risk Signal Identified": "Training Risk Detected",
        "Time Pressure Detected": "Training Timeline Pressure Detected",
        "Critical Concept": "Training Concept Detected",
        "Important Insight": "Performance Insight Detected",
    },
    "sports science": {
        "Key Decision Detected": "Methodology Choice Detected",
        "Critical Issue Flagged": "Methodology Issue Detected",
        "Risk Signal Identified": "Experimental Risk Detected",
        "Time Pressure Detected": "Study Timeline Pressure Detected",
        "Critical Concept": "Methodology Concept Detected",
        "Important Insight": "Research Insight Detected",
    },
    "software engineering": {
        "Key Decision Detected": "Architecture Choice Detected",
        "Critical Issue Flagged": "Implementation Blocker Detected",
        "Risk Signal Identified": "Technical Risk Detected",
        "Time Pressure Detected": "Delivery Pressure Detected",
        "Critical Concept": "Architecture Concern Detected",
        "Important Insight": "Engineering Insight Detected",
    },
    "education": {
        "Key Decision Detected": "Teaching Choice Detected",
        "Critical Issue Flagged": "Learning Blocker Detected",
        "Risk Signal Identified": "Learning Risk Detected",
        "Critical Concept": "Concept Clarification Detected",
        "Important Insight": "Learning Insight Detected",
    },
    "research": {
        "Key Decision Detected": "Research Direction Detected",
        "Critical Issue Flagged": "Methodology Blocker Detected",
        "Risk Signal Identified": "Methodology Risk Detected",
        "Critical Concept": "Hypothesis Framing Detected",
        "Important Insight": "Research Insight Detected",
    },
}


class AlertAgent(BaseAgent):
    """
    Agent that detects key moments and fires alerts.
    Operates via keyword pattern-matching — no LLM required.
    This makes it instant, reliable, and always suitable for live demos.
    """

    def __init__(self, llm=None):
        super().__init__(llm)
        self.alert_history: List[Dict[str, Any]] = []

    def process(self, chunk: str, conversation: Dict[str, Any] = None, conversation_state: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Scan the chunk for alert patterns.
        Returns the full alert history (newest last), capped at 8 entries.
        """
        chunk_lower = chunk.lower()
        domain = (conversation or {}).get("domain", "") if conversation else ""
        domain_key = str(domain).strip().lower()
        state_transitions = (conversation_state or {}).get("semanticTransitions", []) if conversation_state else []
        unresolved_questions = (conversation_state or {}).get("unresolvedQuestions", []) if conversation_state else []
        open_threads = (conversation_state or {}).get("openThreads", []) if conversation_state else []

        if conversation_state:
            if domain_key in ("sports", "sports science"):
                sports_terms = ["activation", "hypertrophy", "compound", "isolation", "recruitment", "training"]
                if any(term in chunk_lower for term in sports_terms):
                    repeated_context = any(
                        any(term in text.lower() for term in sports_terms)
                        for text in unresolved_questions + open_threads + state_transitions
                    )
                    if repeated_context:
                        alert = {
                            "emoji": "🧠",
                            "label": "Training Methodology Uncertainty Detected",
                            "detail": chunk[:120],
                        }
                        self.alert_history = (self.alert_history + [alert])[-8:]
                        return self.alert_history
            if domain_key == "software engineering":
                tech_terms = ["architecture", "latency", "coupling", "consistency", "scalability", "trade-off"]
                if any(term in chunk_lower for term in tech_terms):
                    repeated_context = any(
                        any(term in text.lower() for term in tech_terms)
                        for text in unresolved_questions + open_threads + state_transitions
                    )
                    if repeated_context:
                        alert = {
                            "emoji": "🧭",
                            "label": "Architecture Uncertainty Detected",
                            "detail": chunk[:120],
                        }
                        self.alert_history = (self.alert_history + [alert])[-8:]
                        return self.alert_history
        for pattern in ALERT_PATTERNS:
            if any(kw in chunk_lower for kw in pattern["keywords"]):
                label = pattern["label"]
                # contextualize labels based on conversation domain
                domain_labels = _DOMAIN_ALERT_MAP.get(domain_key, {})
                if label in domain_labels:
                    label = domain_labels[label]
                elif label == "Key Decision Detected" and conversation:
                    mode = (conversation.get("mode", "") or "").lower()
                    if mode not in ("decision making", "making decision"):
                        label = f"Contextual Choice Detected ({domain_key or 'general'})"

                alert: Dict[str, Any] = {
                    "emoji": pattern["emoji"],
                    "label": label,
                    # Show first 120 chars so the UI has context
                    "detail": chunk[:120],
                }
                self.alert_history = (self.alert_history + [alert])[-8:]
                break  # one alert per chunk — highest-priority pattern wins
            # If no direct keyword match, fall through and run light inference heuristics
            # (helps detect timeline pressure, urgency, and implied legal risk)
        if not any(any(kw in chunk_lower for kw in p["keywords"]) for p in ALERT_PATTERNS):
            # Timeline heuristics: presence of time unit + urgency phrasing
            time_terms = ["prazo", "semana", "semanas", "dias", "meses", "deadline", "week", "weeks", "day", "days", "quarter", "trimestre"]
            urgency_terms = ["nao podemos", "não podemos", "cannot", "must", "urgente", "urgent", "imediato", "hoje", "today"]
            if any(t in chunk_lower for t in time_terms) and any(u in chunk_lower for u in urgency_terms):
                alert = {"emoji": "⏳", "label": "Time Pressure Detected", "detail": chunk[:120]}
                self.alert_history = (self.alert_history + [alert])[-8:]
                return self.alert_history

            # Legal/compliance inference: if legal-sounding words appear near risk phrasing
            legal_terms = ["legal", "jurid", "compliance", "conformidade", "lei", "regulatório", "regulatori"]
            if any(lt in chunk_lower for lt in legal_terms) and any(kw in chunk_lower for kw in ["risk", "risco", "liability", "preocup"]):
                alert = {"emoji": "🛡️", "label": "Risk Signal Identified", "detail": chunk[:120]}
                self.alert_history = (self.alert_history + [alert])[-8:]
                return self.alert_history

        return self.alert_history

    def _mock_response(self, prompt: str) -> str:
        # AlertAgent does not call the LLM; pattern matching is always used
        return ""

    def reset(self):
        """Reset alert history."""
        self.alert_history.clear()
