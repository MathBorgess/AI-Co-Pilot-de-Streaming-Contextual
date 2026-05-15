"""Insight Generator Agent - generates contextual insights."""
from typing import List
from .base import BaseAgent


class InsightGeneratorAgent(BaseAgent):
    """Agent that generates insights by connecting content with broader context."""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.all_insights: List[str] = []

    def process(self, chunk: str, context: List[str] = None, conversation: dict = None) -> List[str]:
        """Generate insights based on chunk and retrieved context, adapting to conversation domain."""
        context_str = "\n".join(context or [])
        domain_meta = ''
        if conversation:
            domain_meta = f"Conversation domain: {conversation.get('domain')} | intent: {conversation.get('intent')} | mode: {conversation.get('mode')}\n"

        prompt = f"""You are an insight generator agent. Generate 2-3 actionable insights appropriate to the conversation domain.

{domain_meta}
Current chunk: {chunk}
Related context: {context_str or 'None'}

Generate insights that:
1. Connect patterns across the content
2. Highlight implications for practice
3. Identify emerging trends or connections

Format: Return exactly 2-3 insights, one per line, starting with "→".
Insights:"""

        response = self._call_llm(prompt)
        insights = [line.strip() for line in response.split('\n') if line.strip().startswith('→')]

        if insights:
            self.all_insights = (self.all_insights + insights)[-6:]

        return self.all_insights

    def _mock_response(self, prompt: str) -> str:
        """Mock insights response."""
        insight_templates = [
            "→ AI and streaming technologies are converging to enable real-time intelligent systems.",
            "→ Multi-agent architectures allow specialization, improving overall system performance.",
            "→ RAG bridges the gap between static knowledge and dynamic, real-time context.",
            "→ Event-driven systems naturally align with how AI models process sequential information.",
            "→ Vector databases are becoming essential infrastructure for context-aware AI applications.",
            "→ The combination of WebSockets and AI agents enables truly interactive experiences.",
            "→ Incremental processing reduces latency and allows for faster user feedback loops.",
        ]
        
        prompt_lower = prompt.lower()
        selected = []
        # domain-aware mocks
        if "teaching" in prompt_lower or "education" in prompt_lower:
            selected.append("→ Chunk the concept into 2-3 teaching points and check comprehension at each step.")
        if "research" in prompt_lower or "experiment" in prompt_lower:
            selected.append("→ Consider a minimal experiment to validate the primary hypothesis and measure effect size.")

        if "language" in prompt_lower or "llm" in prompt_lower:
            selected.append("→ Large language models are most effective when given rich, structured context.")
        if "stream" in prompt_lower or "real-time" in prompt_lower:
            selected.append("→ Real-time streaming enables AI systems to respond to changing conditions instantly.")
        if "retrieval" in prompt_lower or "rag" in prompt_lower or "vector" in prompt_lower:
            selected.append("→ RAG significantly improves response quality by grounding LLMs in relevant context.")
        if "agent" in prompt_lower:
            selected.append("→ Specialized agents working in parallel can process information more efficiently than monolithic systems.")
        
        if not selected:
            selected = insight_templates[:2]
        
        return "\n".join(selected[:3])

    def reset(self):
        """Reset the agent state."""
        self.all_insights.clear()
