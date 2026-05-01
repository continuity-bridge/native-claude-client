"""
Event bus for pub/sub event routing.
Central hub for all events in erebos.
"""

from collections import defaultdict
from typing import Dict, List, Callable, Any
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event routing system using pub/sub pattern.

    Subscribers register handlers for specific event types.
    Publishers emit events that get delivered to all subscribers.
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_count = 0

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a handler function for an event type.

        Args:
            event_type: The event type to subscribe to (e.g., "session_start")
            handler: Function that takes event dict as parameter

        Example:
            bus.subscribe("session_start", lambda e: print(f"Session {e['session_id']} started"))
        """
        self.subscribers[event_type].append(handler)
        logger.debug(
            f"Subscribed handler to {event_type}, total handlers: {len(self.subscribers[event_type])}"
        )

    def emit(self, event: Dict[str, Any]):
        """
        Publish an event to all subscribers of its type.

        Args:
            event: Event dictionary with at least "event" key for type

        Example:
            bus.emit({"event": "session_start", "session_id": "abc-123"})
        """
        event_type = event.get("event")
        if not event_type:
            logger.error(f"Event missing 'event' type: {event}")
            return

        self._event_count += 1
        logger.info(f"Emitting {event_type} (#{self._event_count})")

        handlers = self.subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler failed for {event_type}: {e}", exc_info=True)
                # Don't crash - other handlers should still run

    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove a handler from an event type."""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    def clear_all(self):
        """Remove all subscribers (useful for testing)."""
        self.subscribers.clear()
        self._event_count = 0

    @property
    def event_count(self) -> int:
        """Total events emitted since creation."""
        return self._event_count
