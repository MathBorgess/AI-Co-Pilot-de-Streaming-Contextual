"""ConversationDomainAgent - infers conversation domain, subject, intent and mode."""
from typing import List, Dict, Any, Optional
import re
import math
from .base import BaseAgent


class ConversationDomainAgent(BaseAgent):
    """Infers high-level conversation metadata continuously.

    Returns a dict with keys: domain, subject, intent, mode, confidence
    """

    DOMAIN_KEYWORDS = {
        "sports": ["athlete", "training", "reps", "sets", "hypertrophy", "muscle", "coach", "treino", "muscul"],
        "education": ["teach", "lecture", "student", "class", "curriculum", "lesson", "ensinar"],
        "software engineering": ["bug", "deploy", "api", "architecture", "refactor", "service", "backend", "frontend", "pr", "pull request"],
        "legal": ["contract", "law", "legal", "compliance", "jurisdiction", "jurid"],
        "research": ["experiment", "study", "hypothesis", "methodology", "statistical", "p-value", "paper"],
        "product": ["roadmap", "launch", "market", "positioning", "feature", "go-to-market"],
        "incident response": ["incident", "outage", "downtime", "pager", "postmortem", "on-call"],
    }

    INTENT_KEYWORDS = {
        "teaching": ["explain", "teach", "demo", "how to", "how do we"],
        "exploring methodology": ["method", "approach", "protocol", "methodology", "how should we"],
        "solving technical issue": ["bug", "error", "fix", "issue", "fail", "stack trace"],
        "brainstorming": ["ideas", "brainstorm", "ideate", "thoughts", "possibilities"],
        "making decision": ["decide", "decision", "vote", "go/no-go", "final call"],
        "analyzing hypothesis": ["hypothesis", "evidence", "study", "analyze", "results"],
    }

    MODE_KEYWORDS = {
        "brainstorming": ["brainstorm", "ideas", "ideation"],
        "teaching": ["explain", "demo", "walk through", "tutorial"],
        "debate": ["agree", "disagree", "debate", "oppose"],
        "technical discussion": ["implementation", "debug", "stack", "architecture"],
        "analysis": ["analyze", "analysis", "review", "exam"],
        "decision making": ["decide", "decision", "final call"],
        "ideation": ["ideate", "brainstorm"],
    }

    def __init__(self, llm=None):
        super().__init__(llm)
        self.history: List[Dict[str, Any]] = []
        self.conversation_state: Dict[str, Any] = {
            "stableDomain": "general",
            "emergingTopics": [],
            "dominantIntent": "informal discussion",
            "currentMode": "analysis",
            "confidenceTrend": [],
            "unresolvedQuestions": [],
            "semanticTransitions": [],
            "understandingTimeline": [],
            "openThreads": [],
            "topicStability": 0.35,
            "latestSubject": "general topic",
        }
        self._domain_scores: Dict[str, float] = {}
        self._intent_scores: Dict[str, float] = {}
        self._mode_scores: Dict[str, float] = {}
        self._subject_frequency: Dict[str, int] = {}
        self._recent_chunks: List[str] = []

    def _score_map(self, text: str, mapping: Dict[str, List[str]]):
        text_lower = text.lower()
        scores = {}
        for label, kws in mapping.items():
            score = sum(1 for kw in kws if kw in text_lower)
            if score:
                scores[label] = score
        return scores

    def _pick_best(self, scores: Dict[str, int]):
        if not scores:
            return None
        return max(scores.items(), key=lambda x: x[1])[0]

    def _domain_from_scores(self, scores: Dict[str, int]) -> str:
        if not scores:
            return "general"
        return max(scores.items(), key=lambda x: x[1])[0]

    def _intent_from_scores(self, scores: Dict[str, int]) -> str:
        if not scores:
            return "informal discussion"
        return max(scores.items(), key=lambda x: x[1])[0]

    def _mode_from_scores(self, scores: Dict[str, int]) -> str:
        if not scores:
            return "analysis"
        return max(scores.items(), key=lambda x: x[1])[0]

    def _extract_subject(self, chunk: str, context: List[str] = None) -> str:
        # Prefer RAG-provided context if available
        text = (" ".join(context or []) + " " + (chunk or "")).strip()
        # pick longest frequent phrase (naive) — prefer phrases with length > 6
        words = re.findall(r"[a-zA-Z]{4,}", text)
        if not words:
            return "general topic"
        # find most common word longer than 5
        freq = {}
        for w in words:
            w_l = w.lower()
            freq[w_l] = freq.get(w_l, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))
        top = sorted_words[0][0]
        return top.replace('_', ' ')

    def _extract_topics(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text.lower())
        stopwords = {
            "this", "that", "with", "from", "they", "have", "there", "about", "would", "should",
            "because", "these", "those", "where", "when", "what", "which", "their", "while", "into",
            "topic", "today", "again", "need", "need", "could", "should", "after", "before", "through",
        }
        filtered = [t for t in tokens if t not in stopwords]
        freq: Dict[str, int] = {}
        for token in filtered:
            freq[token] = freq.get(token, 0) + 1
        ranked = sorted(freq.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
        return [token for token, _ in ranked[:4]]

    def _update_stability(self, current: str, previous: str, current_score: float) -> float:
        base = self.conversation_state.get("topicStability", 0.35)
        if current == previous:
            base = min(0.95, base + 0.08 * current_score)
        else:
            base = max(0.1, base - 0.1)
        return round(base, 2)

    def _append_unique(self, items: List[str], value: str, limit: int = 5) -> List[str]:
        if not value:
            return items[:limit]
        merged = list(items)
        if value not in merged:
            merged.append(value)
        return merged[-limit:]

    def _transition_label(self, previous: Dict[str, Any], current: Dict[str, Any], stability: float) -> Optional[str]:
        prev_domain = previous.get("stableDomain") or "general"
        prev_intent = previous.get("dominantIntent") or "informal discussion"
        prev_mode = previous.get("currentMode") or "analysis"
        current_domain = current.get("domain") or prev_domain
        current_intent = current.get("intent") or prev_intent
        current_mode = current.get("mode") or prev_mode
        current_subject = current.get("subject") or previous.get("latestSubject") or "topic"

        if current_domain != prev_domain:
            return f"The conversation shifted from {prev_domain} to {current_domain}."
        if current_intent != prev_intent:
            return f"The conversation shifted from {prev_intent} to {current_intent}."
        if current_mode != prev_mode:
            return f"The conversation shifted from {prev_mode} to {current_mode}."
        if stability < 0.45:
            return f"Topic stability decreased after the discussion moved toward {current_subject}."
        if stability > 0.72 and current_subject != previous.get("latestSubject"):
            return f"The conversation deepened around {current_subject}."
        return None

    def process(self, chunk: str, context: List[str] = None) -> Dict[str, Any]:
        """Infer domain/intent/mode from chunk + context and update persistent conversation state."""
        combined = (" ".join(context or []) + " " + (chunk or "")).strip()

        # heuristics scoring
        domain_scores = self._score_map(combined, self.DOMAIN_KEYWORDS)
        intent_scores = self._score_map(combined, self.INTENT_KEYWORDS)
        mode_scores = self._score_map(combined, self.MODE_KEYWORDS)

        # update persistent score memory with semantic inertia
        decay = 0.72
        for domain, score in domain_scores.items():
            self._domain_scores[domain] = self._domain_scores.get(domain, 0.0) * decay + score
        for intent, score in intent_scores.items():
            self._intent_scores[intent] = self._intent_scores.get(intent, 0.0) * decay + score
        for mode, score in mode_scores.items():
            self._mode_scores[mode] = self._mode_scores.get(mode, 0.0) * decay + score

        for domain in list(self._domain_scores.keys()):
            if domain not in domain_scores:
                self._domain_scores[domain] *= decay
        for intent in list(self._intent_scores.keys()):
            if intent not in intent_scores:
                self._intent_scores[intent] *= decay
        for mode in list(self._mode_scores.keys()):
            if mode not in mode_scores:
                self._mode_scores[mode] *= decay

        domain = self._domain_from_scores(self._domain_scores) if self._domain_scores else (self._pick_best(domain_scores) or "general")
        intent = self._intent_from_scores(self._intent_scores) if self._intent_scores else (self._pick_best(intent_scores) or "informal discussion")
        mode = self._mode_from_scores(self._mode_scores) if self._mode_scores else (self._pick_best(mode_scores) or ("decision making" if intent and "decide" in intent else "analysis"))

        subject = self._extract_subject(chunk, context)
        emerging_topics = self._extract_topics(combined)

        # semantic inertia: only flip the stable domain after repeated evidence
        previous_state = dict(self.conversation_state)
        previous_domain = previous_state.get("stableDomain", "general")
        domain_support = self._domain_scores.get(domain, 0.0)
        previous_support = self._domain_scores.get(previous_domain, 0.0)
        if domain == previous_domain or domain_support >= (previous_support * 1.12) or domain_support >= 2.3:
            stable_domain = domain
        else:
            stable_domain = previous_domain

        confidence = min(0.99, 0.12 + 0.18 * (domain_support + self._intent_scores.get(intent, 0.0) + self._mode_scores.get(mode, 0.0)))
        confidence = round(confidence, 2)

        self._subject_frequency[subject] = self._subject_frequency.get(subject, 0) + 1
        stability = self._update_stability(stable_domain, previous_domain, domain_support)
        transition = self._transition_label(
            previous_state,
            {"domain": stable_domain, "intent": intent, "mode": mode, "subject": subject},
            stability,
        )

        if transition:
            self.conversation_state["semanticTransitions"] = self._append_unique(
                self.conversation_state.get("semanticTransitions", []), transition, limit=6
            )

        # confidence trend / evolution
        confidence_trend = list(self.conversation_state.get("confidenceTrend", []))
        confidence_trend.append(confidence)
        confidence_trend = confidence_trend[-8:]

        evolution_events: List[str] = []
        if not self.history:
            evolution_events.append(f"Initial topic: {subject}")
        else:
            last_subject = self.conversation_state.get("latestSubject", "general topic")
            if subject != last_subject:
                evolution_events.append(f"Focus shifted to {subject}")
            if intent != previous_state.get("dominantIntent") and previous_state.get("dominantIntent"):
                evolution_events.append(f"Intent refined toward {intent}")
            if mode != previous_state.get("currentMode") and previous_state.get("currentMode"):
                evolution_events.append(f"Mode shifted to {mode}")
            if confidence >= (confidence_trend[-2] if len(confidence_trend) > 1 else confidence):
                evolution_events.append("Confidence increased after repeated evidence")

        understanding_timeline = list(self.conversation_state.get("understandingTimeline", []))
        for event in evolution_events:
            understanding_timeline = self._append_unique(understanding_timeline, event, limit=8)

        unresolved_questions = list(self.conversation_state.get("unresolvedQuestions", []))
        if stable_domain in ("sports", "sports science"):
            unresolved_questions = [
                q for q in unresolved_questions
                if q not in {
                    "whether activation should precede compound lifts",
                    "if the discussion prioritizes strength or hypertrophy",
                }
            ]
            unresolved_questions = self._append_unique(unresolved_questions, "whether activation should precede compound lifts", limit=5)
            unresolved_questions = self._append_unique(unresolved_questions, "if the discussion prioritizes strength or hypertrophy", limit=5)
        elif stable_domain == "education":
            unresolved_questions = self._append_unique(unresolved_questions, "what level of prior knowledge the audience has", limit=5)
            unresolved_questions = self._append_unique(unresolved_questions, "which concept should be clarified first", limit=5)
        elif stable_domain == "software engineering":
            unresolved_questions = self._append_unique(unresolved_questions, "which constraint matters most: latency, reliability, or coupling", limit=5)
            unresolved_questions = self._append_unique(unresolved_questions, "what trade-off is acceptable for the architecture", limit=5)
        elif stable_domain == "research":
            unresolved_questions = self._append_unique(unresolved_questions, "whether the evidence is strong enough to support the hypothesis", limit=5)
            unresolved_questions = self._append_unique(unresolved_questions, "what would falsify the current idea fastest", limit=5)

        open_threads = list(self.conversation_state.get("openThreads", []))
        for topic in emerging_topics[:3]:
            open_threads = self._append_unique(open_threads, topic, limit=6)

        # memory-aware topic persistence
        self._recent_chunks.append(chunk)
        self._recent_chunks = self._recent_chunks[-6:]

        self.conversation_state.update({
            "stableDomain": stable_domain,
            "emergingTopics": self._append_unique(self.conversation_state.get("emergingTopics", []), subject, limit=6),
            "dominantIntent": intent,
            "currentMode": mode,
            "confidenceTrend": confidence_trend,
            "unresolvedQuestions": unresolved_questions,
            "semanticTransitions": self.conversation_state.get("semanticTransitions", []),
            "understandingTimeline": understanding_timeline,
            "openThreads": open_threads,
            "topicStability": stability,
            "latestSubject": subject,
        })

        # confidence: normalized score sum
        total_hits = sum(domain_scores.values()) + sum(intent_scores.values()) + sum(mode_scores.values())

        meta = {
            "domain": stable_domain,
            "subject": subject,
            "intent": intent,
            "mode": mode,
            "confidence": confidence,
            "conversation_state": self.conversation_state,
            "semanticTransitions": self.conversation_state.get("semanticTransitions", []),
            "understandingTimeline": self.conversation_state.get("understandingTimeline", []),
            "openThreads": self.conversation_state.get("openThreads", []),
        }

        self.history.append(meta)
        # keep history small
        self.history = self.history[-16:]
        return meta

    def reset(self):
        self.history.clear()
        self.conversation_state = {
            "stableDomain": "general",
            "emergingTopics": [],
            "dominantIntent": "informal discussion",
            "currentMode": "analysis",
            "confidenceTrend": [],
            "unresolvedQuestions": [],
            "semanticTransitions": [],
            "understandingTimeline": [],
            "openThreads": [],
            "topicStability": 0.35,
            "latestSubject": "general topic",
        }
        self._domain_scores.clear()
        self._intent_scores.clear()
        self._mode_scores.clear()
        self._subject_frequency.clear()
        self._recent_chunks.clear()
