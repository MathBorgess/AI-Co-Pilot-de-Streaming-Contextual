"""Base agent class."""
import os
from typing import Optional


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, llm=None):
        self.llm = llm
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true" or llm is None

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a prompt."""
        if self.mock_mode or self.llm is None:
            return self._mock_response(prompt)
        try:
            return self.llm.invoke(prompt).content
        except Exception as e:
            print(f"[LLM] Error: {e}, falling back to mock")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Return a mock response for testing."""
        raise NotImplementedError
