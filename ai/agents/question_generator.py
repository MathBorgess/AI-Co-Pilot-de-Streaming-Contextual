"""Question Generator Agent - generates useful questions from the context."""
from typing import List
from .base import BaseAgent


class QuestionGeneratorAgent(BaseAgent):
    """Agent that generates insightful questions about the content."""

    def __init__(self, llm=None):
        super().__init__(llm)
        self.all_questions: List[str] = []

    def process(self, chunk: str, context: List[str] = None, conversation: dict = None) -> List[str]:
        """Generate questions based on new chunk and context."""
        context_str = "\n".join(context or [])
        domain_meta = ''
        if conversation:
            domain_meta = f"Conversation domain: {conversation.get('domain')} | intent: {conversation.get('intent')} | mode: {conversation.get('mode')}\n"

        prompt = f"""You are a question generation agent. Generate 2-3 thought-provoking questions appropriate for the conversation domain.

{domain_meta}
Current chunk: {chunk}
Related context: {context_str or 'None'}

Generate questions that:
1. Explore the key concepts mentioned
2. Encourage deeper thinking
3. Connect ideas from the context

Format: Return exactly 2-3 questions, one per line, starting with "?".
Questions:"""

        response = self._call_llm(prompt)
        questions = [line.strip() for line in response.split('\n') if line.strip().startswith('?')]
        
        if questions:
            # Keep only the latest 5 most relevant questions
            self.all_questions = (self.all_questions + questions)[-5:]
        
        return self.all_questions

    def _mock_response(self, prompt: str) -> str:
        """Mock questions response."""
        question_templates = [
            "? How does this concept apply to real-world systems?",
            "? What are the key challenges when implementing this approach?",
            "? How does streaming processing differ from batch processing in this context?",
            "? What role does context play in improving AI response quality?",
            "? How can multi-agent systems improve the accuracy of results?",
            "? What are the scalability implications of this architecture?",
            "? How would you handle failures in a distributed streaming pipeline?",
        ]
        
        # Select questions based on content
        chunk_lower = prompt.lower()
        selected = []
        
        # domain-aware mocks
        if "teaching" in prompt.lower() or "education" in prompt.lower():
            selected.append("? Can you restate the core idea in simpler terms for learners?")
        if "research" in prompt.lower() or "experiment" in prompt.lower():
            selected.append("? What is the key hypothesis and how would you test it?")
        if "sports" in prompt.lower() or "training" in prompt.lower():
            selected.append("? What measurable performance metric should we track?")
        if "ai" in chunk_lower or "machine learning" in chunk_lower:
            selected.append("? How does this concept apply to real-world AI systems?")
        if "stream" in chunk_lower:
            selected.append("? How does streaming processing differ from batch processing in this context?")
        if "agent" in chunk_lower:
            selected.append("? How can multi-agent systems improve the accuracy of results?")
        if "vector" in chunk_lower or "rag" in chunk_lower:
            selected.append("? What are the advantages of using vector databases for context retrieval?")
        
        if not selected:
            selected = question_templates[:2]
        
        return "\n".join(selected[:3])

    def reset(self):
        """Reset the agent state."""
        self.all_questions.clear()
