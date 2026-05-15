"""Action Agent - suggests concrete next steps based on streaming context."""
from typing import List, Dict, Optional
from .base import BaseAgent

_ACTION_MAP: Dict[str, List[str]] = {
    "decision": [
        "The AI recommends assigning a clear decision owner before this meeting ends.",
        "The AI recommends setting a go/no-go checkpoint with explicit success criteria.",
        "The AI recommends documenting decision criteria and circulating them for quick sign-off.",
    ],
    "risk": [
        "The AI recommends running a focused risk review and capturing mitigation owners.",
        "The AI recommends clarifying legal/compliance ownership before approving launch.",
        "The AI recommends defining a rollback path in case this risk materializes.",
    ],
    "deadline": [
        "The AI recommends locking the critical path and confirming dependency readiness.",
        "The AI recommends trimming scope to protect the committed delivery date.",
        "The AI recommends weekly decision checkpoints until the deadline risk drops.",
    ],
    "conflict": [
        "The AI recommends a time-boxed evidence spike to resolve this disagreement.",
        "The AI recommends documenting both positions and aligning asynchronously.",
        "The AI recommends escalating to a neutral decision owner if alignment stalls.",
    ],
    "competitor": [
        "The AI recommends a rapid competitive teardown to clarify differentiation.",
        "The AI recommends aligning a counter-positioning message across go-to-market teams.",
    ],
    "financial": [
        "The AI recommends validating the investment threshold with a quick ROI check.",
        "The AI recommends confirming budget ownership before committing resources.",
    ],
    "concept": [
        "The AI recommends converting this concept into a one-page decision memo.",
        "The AI recommends validating architecture assumptions in a short review.",
    ],
    "insight": [
        "The AI recommends turning this insight into a measurable experiment.",
        "The AI recommends sharing this learning quickly to accelerate alignment.",
    ],
    "default": [
        "The AI recommends capturing explicit owners for every open action.",
        "The AI recommends scheduling a short follow-up to validate assumptions.",
    ],
}

_ALERT_TO_CATEGORY = {
    "Key Decision Detected": "decision",
    "Critical Issue Flagged": "risk",
    "Time Pressure Detected": "deadline",
    "Team Conflict Detected": "conflict",
    "Competitive Signal": "competitor",
    "Financial Implication": "financial",
    "Critical Concept": "concept",
    "Important Insight": "insight",
}

_DOMAIN_ACTION_MAP: Dict[str, Dict[str, List[str]]] = {
    "sports": {
        "brainstorming": [
            "The AI recommends comparing 2-3 training hypotheses before changing the program.",
            "The AI recommends keeping the question tied to performance outcomes, not just exercise preference.",
        ],
        "teaching": [
            "The AI recommends explaining the movement pattern before discussing programming details.",
            "The AI recommends using a simple training example to ground the concept.",
        ],
        "technical discussion": [
            "The AI recommends checking whether activation quality changes with load, order, or fatigue.",
            "The AI recommends validating the claim against a concrete performance measure.",
        ],
        "analysis": [
            "The AI recommends narrowing the discussion to the training variable that matters most.",
            "The AI recommends separating observation, interpretation, and conclusion.",
        ],
        "decision making": [
            "The AI recommends deciding which training variable to test first.",
            "The AI recommends defining the success metric before changing the program.",
        ],
    },
    "sports science": {
        "technical discussion": [
            "The AI recommends validating whether muscle recruitment changes with exercise order.",
            "The AI recommends comparing isolation and compound lifts using the same measurement method.",
        ],
        "analysis": [
            "The AI recommends separating the hypothesis from the observed training signal.",
            "The AI recommends identifying which variable is most likely driving the change.",
        ],
    },
    "software engineering": {
        "technical discussion": [
            "The AI recommends isolating the bottleneck with a focused reproduction test.",
            "The AI recommends validating the coupling, consistency, or latency assumption directly.",
        ],
        "analysis": [
            "The AI recommends reducing the system to the smallest failing path.",
            "The AI recommends comparing the trade-off between correctness, speed, and complexity.",
        ],
        "decision making": [
            "The AI recommends choosing the architectural option that best matches the observed constraint.",
            "The AI recommends documenting the trade-off before making the final call.",
        ],
    },
    "education": {
        "teaching": [
            "The AI recommends clarifying the core concept before moving to examples.",
            "The AI recommends checking whether the explanation matches the learner's level.",
        ],
        "brainstorming": [
            "The AI recommends generating a few ways to make the concept easier to teach.",
            "The AI recommends testing which explanation format improves comprehension.",
        ],
    },
    "research": {
        "analysis": [
            "The AI recommends separating the hypothesis from the result interpretation.",
            "The AI recommends checking whether the evidence is strong enough to support the claim.",
        ],
        "technical discussion": [
            "The AI recommends validating the methodology with a smaller controlled test.",
            "The AI recommends confirming the measurement approach before drawing conclusions.",
        ],
        "brainstorming": [
            "The AI recommends proposing 2-3 competing hypotheses to test next.",
            "The AI recommends choosing the experiment that will falsify the idea fastest.",
        ],
    },
    "product": {
        "decision making": [
            "The AI recommends aligning on the decision owner and the launch criteria.",
            "The AI recommends writing down the trade-off before the team commits.",
        ],
    },
}

_DOMAIN_ALERT_MAP: Dict[str, Dict[str, str]] = {
    "sports": {
        "Key Decision Detected": "Training Method Decision Detected",
        "Risk Signal Identified": "Training Risk Signal Detected",
        "Critical Concept": "Training Concept Detected",
        "Important Insight": "Performance Insight Detected",
        "Time Pressure Detected": "Training Timeline Pressure Detected",
    },
    "sports science": {
        "Key Decision Detected": "Methodology Choice Detected",
        "Risk Signal Identified": "Experimental Risk Detected",
        "Critical Concept": "Methodology Concept Detected",
        "Important Insight": "Research Insight Detected",
    },
    "software engineering": {
        "Key Decision Detected": "Architecture Choice Detected",
        "Risk Signal Identified": "Technical Risk Detected",
        "Critical Concept": "Architecture Concern Detected",
        "Important Insight": "Implementation Insight Detected",
    },
    "education": {
        "Key Decision Detected": "Teaching Choice Detected",
        "Critical Concept": "Concept Clarification Detected",
        "Important Insight": "Learning Insight Detected",
    },
    "research": {
        "Key Decision Detected": "Research Direction Detected",
        "Risk Signal Identified": "Methodology Risk Detected",
        "Critical Concept": "Hypothesis Framing Detected",
        "Important Insight": "Research Insight Detected",
    },
}


def _normalize_domain(conversation: Optional[dict]) -> str:
    if not conversation:
        return ""
    return (conversation.get("domain") or "").strip().lower()


def _normalize_mode(conversation: Optional[dict]) -> str:
    if not conversation:
        return ""
    return (conversation.get("mode") or "").strip().lower()


def _detect_category(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in ["decide", "decision", "final call", "vote", "commit to", "go/no-go", "decisao", "decidir", "voto"]):
        return "decision"
    if any(kw in t for kw in ["risk", "legal", "compliance", "flagged", "blocker", "risco", "juridico", "conformidade", "bloqueador"]):
        return "risk"
    if any(kw in t for kw in ["deadline", "cannot slip", "ship", "launch", "quarter", "prazo", "nao podemos atrasar", "lancar", "trimestre"]):
        return "deadline"
    if any(kw in t for kw in ["split", "conflict", "disagree", "tension", "push back", "conflito", "discorda", "tensao", "dividido"]):
        return "conflict"
    if any(kw in t for kw in ["competitor", "competition", "market", "losing", "traction", "concorrente", "competicao", "mercado", "perdendo"]):
        return "competitor"
    if any(kw in t for kw in ["budget", "cost", "invest", "revenue", "financial", "roi", "orcamento", "custo", "receita"]):
        return "financial"
    if any(kw in t for kw in ["architecture", "strategy", "roadmap", "platform", "trade-off", "escopo", "arquitetura", "estrategia"]):
        return "concept"
    if any(kw in t for kw in ["insight", "signal", "pattern", "learning", "insight", "sinal", "padrao", "aprendizado"]):
        return "insight"
    return "default"


class ActionAgent(BaseAgent):
    """Agent that suggests next steps and recommended actions."""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.current_actions: List[str] = []

    def process(self, chunk: str, context: List[str] = None, recent_alerts: List[dict] = None, conversation: Optional[dict] = None, conversation_state: Optional[dict] = None) -> List[str]:
        """Generate recommended actions based on the chunk, context, and recent alerts."""
        alert_labels = [a.get("label", "") for a in (recent_alerts or [])]
        domain_blob = ''
        if conversation:
            domain_blob = f"Conversation domain: {conversation.get('domain')} | intent: {conversation.get('intent')} | mode: {conversation.get('mode')} | subject: {conversation.get('subject')}\n"
        state_blob = ''
        if conversation_state:
            transitions = '; '.join(conversation_state.get('semanticTransitions', [])[-3:]) or 'none'
            unresolved = '; '.join(conversation_state.get('unresolvedQuestions', [])[-3:]) or 'none'
            threads = '; '.join(conversation_state.get('openThreads', [])[-3:]) or 'none'
            state_blob = (
                f"Conversation state: stableDomain={conversation_state.get('stableDomain')} | currentMode={conversation_state.get('currentMode')} | "
                f"dominantIntent={conversation_state.get('dominantIntent')} | confidenceTrend={conversation_state.get('confidenceTrend', [])[-4:]} | "
                f"semanticTransitions={transitions} | unresolvedQuestions={unresolved} | openThreads={threads}\n"
            )

        prompt = (
            "You are an action agent for a live conversation copilot.\n"
            "Adapt tone and recommended next steps to the conversation domain, intent and mode.\n"
            "Use the conversation state to preserve continuity across chunks.\n"
            "Be tolerant to imperfect transcription and focus on meaning.\n"
            "Generate 2-3 concrete, practical next steps appropriate for the context.\n\n"
            f"{domain_blob}"
            f"{state_blob}"
            f"Content: {chunk}\n"
            f"Related context: {', '.join(context or []) or 'None'}\n"
            f"Recent alerts: {alert_labels or 'none'}\n\n"
            "Format: Return exactly 2-3 action items, one per line, starting with '→'.\n"
            "Actions:"
        )
        response = self._call_llm(prompt)
        actions = [line.strip() for line in response.split("\n")
                   if line.strip().startswith("→")]
        if actions:
            self.current_actions = actions[:3]
        return self.current_actions

    def _mock_response(self, prompt: str) -> str:
        """Keyword-driven mock actions."""
        prompt_l = prompt.lower()

        domain = ""
        mode = ""
        subject = ""
        state_text = ""
        for line in prompt.splitlines():
            lower = line.lower()
            if lower.startswith("conversation domain:"):
                pieces = line.split("|")
                for piece in pieces:
                    if "conversation domain:" in piece.lower():
                        domain = piece.split(":", 1)[1].strip().lower()
                    elif "mode:" in piece.lower():
                        mode = piece.split(":", 1)[1].strip().lower()
                    elif "subject:" in piece.lower():
                        subject = piece.split(":", 1)[1].strip().lower()
            if lower.startswith("conversation state:"):
                state_text = line

        if state_text:
            if "semantictransitions=" in state_text.lower() and "none" not in state_text.lower():
                if domain in ("sports", "sports science"):
                    return "\n".join([
                        "→ Bridge the recent shift explicitly before adding a new training hypothesis.",
                        "→ Re-anchor the discussion on activation, exercise order, and the current performance goal.",
                    ])
                if domain == "software engineering":
                    return "\n".join([
                        "→ Re-state the last architecture shift and validate the new constraint before moving on.",
                        "→ Compare the current option against the previously discussed trade-off to keep continuity.",
                    ])

            if "unresolvedquestions=" in state_text.lower() and "none" not in state_text.lower():
                if domain in ("sports", "sports science"):
                    return "\n".join([
                        "→ Test whether activation should come before compound lifts using a small controlled comparison.",
                        "→ Clarify whether the immediate goal is strength gain or hypertrophy before changing the program.",
                    ])
                if domain == "education":
                    return "\n".join([
                        "→ Clarify the learner's starting point before introducing the next concept.",
                        "→ Align the explanation with the evaluation criteria so the lesson stays coherent.",
                    ])

        domain_bucket = _DOMAIN_ACTION_MAP.get(domain, {})
        mode_bucket = domain_bucket.get(mode) or domain_bucket.get("analysis") or domain_bucket.get("decision making")

        if mode_bucket:
            return "\n".join(f"→ {t}" for t in mode_bucket[:2])

        # Decision-making branch must surface owners/compliance when present
        if "decision" in prompt_l or "making decision" in prompt_l or "go/no-go" in prompt_l:
            return "\n".join([
                "→ Assign a clear owner for the next choice and capture success criteria.",
                "→ Confirm the validation step or evidence needed before proceeding.",
            ])

        # If conversation mode suggests teaching / brainstorming / research, adapt
        if "teaching" in prompt_l or "explain" in prompt_l:
            return "\n".join(["→ Provide a short, clear explanation focusing on the core concept.", "→ Offer a simple example or analogy to aid understanding."])
        if "brainstorm" in prompt_l or "ideation" in prompt_l:
            return "\n".join(["→ List 2-3 hypothesis or idea directions to explore.", "→ Prioritize based on feasibility and impact."])
        if "research" in prompt_l or "experiment" in prompt_l or "hypothesis" in prompt_l:
            return "\n".join(["→ Suggest a small experiment to validate the hypothesis.", "→ Define measurable outcome and quick success criteria."])
        if "technical" in prompt_l or "bug" in prompt_l or "architecture" in prompt_l:
            return "\n".join(["→ Propose a focused technical validation or test to reproduce the issue.", "→ Identify the smallest safe change to validate the assumption."])

        # fallback to alert-driven category if present
        for label, category in _ALERT_TO_CATEGORY.items():
            if label.lower() in prompt_l:
                templates = _ACTION_MAP[category]
                return "\n".join(f"→ {t}" for t in templates[:2])

        category = _detect_category(prompt)
        templates = _ACTION_MAP.get(category, _ACTION_MAP["default"])
        return "\n".join(f"→ {t}" for t in templates[:2])

    def reset(self):
        """Reset agent state."""
        self.current_actions.clear()
