"""Direction Agent - backwards-compatible alias of ActionAgent."""
from .action_agent import ActionAgent


class DirectionAgent(ActionAgent):
    """Deprecated: use ActionAgent. This alias preserves compatibility."""

    @property
    def current_directions(self):
        return self.current_actions

    def reset(self):
        super().reset()
