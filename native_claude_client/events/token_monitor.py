"""
Monitors token usage and emits threshold crossing events.
"""

from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


class TokenMonitor:
    """
    Tracks token usage and emits events at threshold percentages.

    Thresholds: 60%, 80%, 85%, 90%
    Each threshold only emits once per session.
    """

    def __init__(self, event_bus, max_tokens: int = 200000):
        self.bus = event_bus
        self.max_tokens = max_tokens
        self.current_tokens = 0
        self.message_count = 0
        self.crossed = {60: False, 80: False, 85: False, 90: False}

    def update(self, token_count: int):
        """
        Update current token count and emit threshold events if crossed.

        Args:
            token_count: Total tokens used in session
        """
        self.current_tokens = token_count
        self.message_count += 1

        percentage = (token_count / self.max_tokens) * 100

        for threshold in [60, 80, 85, 90]:
            if percentage >= threshold and not self.crossed[threshold]:
                self._emit_threshold(threshold, percentage)
                self.crossed[threshold] = True

    def _emit_threshold(self, threshold: int, percentage: float):
        """Emit token_threshold event."""
        event = {
            "event": "token_threshold",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "percentage": percentage,
            "threshold_crossed": threshold,
            "messages_count": self.message_count,
        }

        logger.warning(
            f"Token threshold {threshold}% crossed " f"({self.current_tokens}/{self.max_tokens})"
        )
        self.bus.emit(event)

    def reset(self):
        """Reset for new session."""
        self.current_tokens = 0
        self.message_count = 0
        self.crossed = {60: False, 80: False, 85: False, 90: False}

    @property
    def percentage_used(self) -> float:
        """Current usage percentage."""
        return (self.current_tokens / self.max_tokens) * 100
