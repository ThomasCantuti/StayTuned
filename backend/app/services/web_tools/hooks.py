"""Hooks for controlling the scraper agent loop behavior."""

import logging
from strands.hooks.registry import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent

logger = logging.getLogger(__name__)


class MaxToolCallsHook(HookProvider):
    """Prevents infinite agent loops by limiting the total number of tool calls per invocation.

    When the limit is reached, the hook cancels additional tool calls, forcing the model
    to produce a final answer with whatever information it has gathered so far.
    """

    def __init__(self, max_calls: int = 6):
        self.max_calls = max_calls
        self._call_count = 0

    def reset(self):
        """Reset the counter. Call this before each new agent invocation."""
        self._call_count = 0

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(None, self._before_tool_call)

    def _before_tool_call(self, event: BeforeToolCallEvent) -> None:
        self._call_count += 1
        tool_name = event.tool_use.get("name", "unknown")
        logger.info(f"[MaxToolCallsHook] Tool call #{self._call_count}/{self.max_calls}: {tool_name}")

        if self._call_count > self.max_calls:
            logger.warning(
                f"[MaxToolCallsHook] Limit reached ({self.max_calls} calls). "
                f"Cancelling tool '{tool_name}' to force final answer."
            )
            event.cancel_tool = (
                f"TOOL CALL LIMIT REACHED ({self.max_calls} calls). "
                "You MUST now produce your final structured response using the information "
                "you have gathered so far. Do NOT call any more tools."
            )
