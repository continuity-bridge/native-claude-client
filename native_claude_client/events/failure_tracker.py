"""
Tracks tool failure patterns and emits threshold events.
"""

import time
from collections import defaultdict
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class FailureTracker:
    """
    Monitors tool failures and emits failure_threshold events.

    Tracks:
    - Consecutive failures per tool family
    - Failure velocity (failures per minute)
    - Domain-specific thresholds
    """

    def __init__(self, event_bus, config: Dict):
        self.bus = event_bus
        self.config = config

        # State tracking
        self.failures: Dict[str, int] = defaultdict(int)  # family -> count
        self.failure_times: Dict[str, List[float]] = defaultdict(list)  # family -> [timestamps]
        self.last_success: Dict[str, float] = {}  # family -> timestamp

        # Subscribe to tool failures and successes
        self.bus.subscribe("tool_call_failed", self.on_tool_failed)
        self.bus.subscribe("tool_call_success", self.on_tool_success)

    def on_tool_failed(self, event):
        """Handle tool_call_failed event."""
        family = event["tool_family"]
        domain = event.get("domain", "default")

        # Reset count if last call succeeded
        if family in self.last_success:
            self.failures[family] = 0
            del self.last_success[family]

        # Increment failure count
        self.failures[family] += 1

        # Track timing for velocity calculation
        now = time.time()
        self.failure_times[family].append(now)

        # Calculate velocity (failures in last 60s)
        recent = [t for t in self.failure_times[family] if now - t < 60]
        self.failure_times[family] = recent  # Keep only recent
        velocity = len(recent)  # failures per minute

        # Get threshold for this family/domain
        threshold = self._get_threshold(family, domain)

        # Velocity-based adjustment
        adjusted_threshold = threshold
        if velocity >= 10:  # High velocity
            adjusted_threshold = max(1, int(threshold * 0.5))

        logger.debug(
            f"{family}: {self.failures[family]} failures "
            f"(threshold: {adjusted_threshold}, velocity: {velocity}/min)"
        )

        # Check if threshold reached
        if self.failures[family] >= adjusted_threshold:
            self._emit_threshold_event(family, domain, threshold, adjusted_threshold, velocity)
            # Reset after threshold
            self.failures[family] = 0

    def on_tool_success(self, event):
        """Handle tool_call_success event."""
        family = event["tool_family"]
        self.last_success[family] = time.time()

    def _get_threshold(self, family: str, domain: str) -> int:
        """Get threshold from config, domain-specific or default."""
        thresholds = self.config.get("tool_family_thresholds", {})

        # Try domain-specific first
        if domain in thresholds and family in thresholds[domain]:
            return thresholds[domain][family]

        # Fall back to default
        if "default" in thresholds and family in thresholds["default"]:
            return thresholds["default"][family]

        # Ultimate fallback
        return 3

    def _emit_threshold_event(self, family, domain, threshold, adjusted_threshold, velocity):
        """Emit failure_threshold event."""
        event = {
            "event": "failure_threshold",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tool_family": family,
            "consecutive_failures": self.failures[family],
            "threshold": threshold,
            "failure_velocity": velocity,
            "velocity_adjusted_threshold": adjusted_threshold,
            "domain": domain,
        }

        logger.warning(f"Failure threshold reached for {family}: {self.failures[family]} failures")
        self.bus.emit(event)
