"""
Hook executor engine - loads registry and executes hooks on events.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HookExecutor:
    """
    Loads hook registry and config, subscribes to events, executes hooks.

    Phase 2: Stub implementation that logs execution without running actual hooks.
    Phase 3: Will parse executor markdown and run steps.
    """

    def __init__(
        self, event_bus, registry_path: Optional[str] = None, config_path: Optional[str] = None
    ):
        self.bus = event_bus
        self.registry = self._load_registry(registry_path)
        self.config = self._load_config(config_path)
        self.enabled_hooks = self.config.get("enabled_hooks", [])
        self.execution_log = []

        self._subscribe_hooks()

    def _load_registry(self, path: Optional[str]) -> Dict:
        """Load hooks registry from JSON file."""
        if path and Path(path).exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry from {path}: {e}")
                return {"hooks": []}

        # Return default empty registry if no path or file not found
        return {"hooks": []}

    def _load_config(self, path: Optional[str]) -> Dict:
        """Load hooks config from JSON file."""
        if path and Path(path).exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config from {path}: {e}")
                return {"enabled_hooks": []}

        # Return default config if no path or file not found
        return {"enabled_hooks": []}

    def _subscribe_hooks(self):
        """Subscribe enabled hooks to their trigger events."""
        for hook in self.registry.get("hooks", []):
            if hook["id"] not in self.enabled_hooks:
                continue

            trigger_type = hook["trigger"]["type"]

            # Create handler for this hook
            handler = lambda event, h=hook: self._execute_hook(h, event)

            self.bus.subscribe(trigger_type, handler)
            logger.info(f"Subscribed hook '{hook['id']}' to event '{trigger_type}'")

    def _execute_hook(self, hook: Dict, event: Dict[str, Any]):
        """Execute a hook when its event fires."""
        hook_id = hook["id"]

        # Check if conditions met
        if not self._conditions_met(hook, event):
            logger.debug(f"Hook '{hook_id}' conditions not met, skipping")
            return

        # Check if should prompt before execution
        if hook.get("prompt_before", False):
            logger.info(f"Hook '{hook_id}' requires prompt - skipping automatic execution")
            return

        logger.info(f"Executing hook '{hook_id}'")

        try:
            # Phase 2: Log execution (stub)
            # Phase 3: Parse executor markdown and run steps
            logger.info(f"[STUB] Would execute: {hook.get('executor', 'No executor defined')}")

            # Log execution
            self._log_execution(hook_id, event, success=True)

        except Exception as e:
            logger.error(f"Hook '{hook_id}' execution failed: {e}", exc_info=True)
            self._log_execution(hook_id, event, success=False, error=str(e))

    def _conditions_met(self, hook: Dict, event: Dict) -> bool:
        """
        Check if hook conditions are satisfied.

        Phase 2: Simple implementation - just checks event type matches.
        Phase 3: Full condition parsing (tool_family, domain, etc.)
        """
        # For now, assume conditions are met if event type matches
        # Phase 3 will implement full condition parsing
        return True

    def _log_execution(self, hook_id: str, event: Dict, success: bool, error: str = None):
        """Log hook execution to in-memory list and optionally JSONL."""
        log_entry = {
            "timestamp": event.get("timestamp"),
            "session_id": event.get("session_id"),
            "event_type": event.get("event"),
            "hook_id": hook_id,
            "execution_status": "success" if success else "failed",
            "error_message": error,
        }

        self.execution_log.append(log_entry)

        # Optionally write to JSONL file if logs directory exists
        # This is handled by the client, not the library

    def get_execution_history(self) -> list:
        """Get execution history for this session."""
        return self.execution_log.copy()
