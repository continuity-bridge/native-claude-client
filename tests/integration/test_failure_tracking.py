"""
Integration tests for event system with FailureTracker.
"""

import pytest
from erebos.events.bus import EventBus
from erebos.events.emitter import EventEmitter
from erebos.events.failure_tracker import FailureTracker
from erebos.llm.ollama_client import OllamaClient
from tests.events.test_config import get_test_config


def test_failure_tracker_integration():
    """Test FailureTracker integrated with EventBus and EventEmitter."""
    bus = EventBus()
    emitter = EventEmitter(bus)
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    # Track threshold events
    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Start a session
    emitter.start_session(domain="default")

    # Simulate 3 tool failures
    for i in range(3):
        emitter.tool_failed(
            tool_name="Filesystem:read_file",
            tool_family="Filesystem",
            error_type="not_loaded",
            error_message="Tool has not been loaded yet",
        )

    # Should have triggered threshold
    assert len(threshold_events) == 1
    assert threshold_events[0]["tool_family"] == "Filesystem"
    assert threshold_events[0]["consecutive_failures"] == 3

    # End session
    emitter.end_session("test_complete")


def test_ollama_failure_tracking():
    """Test that OllamaClient failures are tracked properly."""
    bus = EventBus()
    emitter = EventEmitter(bus)
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    client = OllamaClient()
    client.event_emitter = emitter

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    emitter.start_session(domain="default")

    # Try to use non-existent model 3 times (will fail)
    for i in range(3):
        try:
            client.chat("nonexistent-model", "test")
        except Exception:
            pass  # Expected to fail

    # Should have triggered threshold for ollama family
    assert len(threshold_events) == 1
    assert threshold_events[0]["tool_family"] == "ollama"


def test_mixed_success_and_failure():
    """Test realistic pattern of successes and failures."""
    bus = EventBus()
    emitter = EventEmitter(bus)
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    emitter.start_session(domain="default")

    # Pattern: fail, fail, success, fail, fail, fail (should trigger)
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "timeout", "Timeout")
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "timeout", "Timeout")
    emitter.tool_succeeded("Filesystem:read_file", "Filesystem")  # Reset
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "timeout", "Timeout")
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "timeout", "Timeout")
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "timeout", "Timeout")

    # Should trigger after the 3 consecutive failures
    assert len(threshold_events) == 1

    emitter.end_session("test_complete")
