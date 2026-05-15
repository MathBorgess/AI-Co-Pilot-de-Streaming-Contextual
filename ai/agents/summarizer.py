"""Summarizer Agent - maintains cumulative summary state."""
from typing import List
from .base import BaseAgent


class SummarizerAgent(BaseAgent):
    """Agent that maintains an incremental summary of the stream."""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.accumulated_chunks: List[str] = []
        self.current_summary: str = ""

    def process(self, chunk: str, context: List[str] = None, conversation: dict = None) -> str:
        """Process a new chunk and update the summary. Accept conversation metadata to adapt tone.
        """
        self.accumulated_chunks.append(chunk)
        context_str = "\n".join(context or [])
        domain_meta = ''
        if conversation:
            domain_meta = f"Conversation domain: {conversation.get('domain')} | intent: {conversation.get('intent')} | mode: {conversation.get('mode')}\n"

        prompt = f"""You are a summarizer agent. Create a concise, cumulative summary adapted to the conversation domain.

{domain_meta}
Previous summary: {self.current_summary or 'None yet'}
New chunk: {chunk}
Related context: {context_str or 'None'}

Update the summary to include the new information. Keep it under 3 sentences. Be concise and clear.
Summary:"""

        self.current_summary = self._call_llm(prompt)
        return self.current_summary

    def _mock_response(self, prompt: str) -> str:
        """Mock summary response."""
        chunk_count = len(self.accumulated_chunks)
        topics = []
        keywords = ["AI", "machine learning", "streaming", "agent", "vector", "language", "event", "real-time"]
        for keyword in keywords:
            if keyword.lower() in " ".join(self.accumulated_chunks).lower():
                topics.append(keyword)

        if not topics:
            topics = ["technology", "systems"]

        if chunk_count == 1:
            return f"The content introduces concepts related to {', '.join(topics[:2])}."
        elif chunk_count <= 3:
            return f"The discussion covers {', '.join(topics[:3])}, exploring their interconnections and applications in modern systems."
        else:
            return f"This comprehensive overview addresses {', '.join(topics[:4])}, examining how these technologies work together to enable intelligent, real-time systems capable of processing continuous data streams."

    def reset(self):
        """Reset the agent state."""
        self.accumulated_chunks.clear()
        self.current_summary = ""
