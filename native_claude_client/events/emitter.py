"""
Event emitter for detecting conditions and publishing events.
"""

import uuid
from datetime import datetime, UTC
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EventEmitter:
    """
    Detects conditions and emits events to the EventBus.

    No business logic - just detection and emission.
    Hook executors handle the actual work.
    """

    def __init__(self, event_bus):
        self.bus = event_bus
        self.session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None

    def start_session(self, domain: str = "default", prior_session_id: Optional[str] = None):
        """
        Emit session_start event for new conversation.

        Args:
            domain: Domain identifier (e.g., "domain_1_professional")
            prior_session_id: UUID of previous session if resuming
        """
        self.session_id = str(uuid.uuid4())
        self.session_start_time = datetime.now(UTC)

        event = {
            "event": "session_start",
            "timestamp": self.session_start_time.isoformat().replace("+00:00", "Z"),
            "session_id": self.session_id,
            "platform": "native-claude-client",
            "domain": domain,
            "prior_session_id": prior_session_id,
        }

        logger.info(f"Starting session {self.session_id} in domain {domain}")
        self.bus.emit(event)

    def end_session(self, trigger: str = "user_keyword"):
        """
        Emit session_end event.

        Args:
            trigger: What caused session end ("user_keyword", "inactivity", "app_close")
        """
        if not self.session_id:
            logger.warning("end_session called but no session active")
            return

        duration = (datetime.now(UTC) - self.session_start_time).total_seconds()

        event = {
            "event": "session_end",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "session_id": self.session_id,
            "trigger": trigger,
            "duration_seconds": duration,
        }

        logger.info(f"Ending session {self.session_id} (duration: {duration:.1f}s)")
        self.bus.emit(event)

    def tool_failed(self, tool_name: str, tool_family: str, error_type: str, error_message: str):
        """
        Emit tool_call_failed event.

        Args:
            tool_name: Full tool name (e.g., "Filesystem:read_file")
            tool_family: Tool family (e.g., "Filesystem")
            error_type: Error classification ("not_loaded", "timeout", "api_error")
            error_message: Error description
        """
        event = {
            "event": "tool_call_failed",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "session_id": self.session_id,
            "tool_name": tool_name,
            "tool_family": tool_family,
            "error_type": error_type,
            "error_message": error_message,
        }

        logger.warning(f"Tool {tool_name} failed: {error_type}")
        self.bus.emit(event)

    def tool_succeeded(self, tool_name: str, tool_family: str):
        """
        Emit tool_call_success event to reset failure counters.

        Args:
            tool_name: Full tool name
            tool_family: Tool family
        """
        event = {
            "event": "tool_call_success",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "session_id": self.session_id,
            "tool_name": tool_name,
            "tool_family": tool_family,
        }

        logger.debug(f"Tool {tool_name} succeeded")
        self.bus.emit(event)
