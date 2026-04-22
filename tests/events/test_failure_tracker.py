"""
Unit tests for FailureTracker.
"""

import time
import pytest
from native_claude_client.events.bus import EventBus
from native_claude_client.events.failure_tracker import FailureTracker
from tests.events.test_config import get_test_config


def test_threshold_detection():
    """Test that threshold event emits after N failures."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Simulate 3 consecutive failures (default threshold)
    for i in range(3):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "default",
            }
        )

    assert len(threshold_events) == 1
    assert threshold_events[0]["tool_family"] == "Filesystem"
    assert threshold_events[0]["consecutive_failures"] == 3


def test_success_resets_counter():
    """Test that success resets failure counter."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Fail twice
    for i in range(2):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "default",
            }
        )

    # Success resets
    bus.emit(
        {
            "event": "tool_call_success",
            "tool_family": "Filesystem",
        }
    )

    # Fail twice more - shouldn't hit threshold yet
    for i in range(2):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "default",
            }
        )

    # Should not have triggered threshold (only 2 consecutive)
    assert len(threshold_events) == 0


def test_domain_specific_threshold():
    """Test domain-specific thresholds work."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Professional domain has threshold of 2 for Filesystem
    for i in range(2):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "domain_1_professional",
            }
        )

    # Should trigger at 2 failures
    assert len(threshold_events) == 1
    assert threshold_events[0]["threshold"] == 2


def test_separate_family_tracking():
    """Test that different tool families are tracked separately."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Fail Filesystem twice
    for i in range(2):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "default",
            }
        )

    # Fail Notion twice
    for i in range(2):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Notion",
                "domain": "default",
            }
        )

    # Neither should have hit threshold (both at 2, threshold is 3)
    assert len(threshold_events) == 0

    # One more Filesystem failure should trigger
    bus.emit(
        {
            "event": "tool_call_failed",
            "tool_family": "Filesystem",
            "domain": "default",
        }
    )

    assert len(threshold_events) == 1
    assert threshold_events[0]["tool_family"] == "Filesystem"


def test_velocity_calculation():
    """Test failure velocity is calculated correctly."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Rapid failures (simulate high velocity)
    for i in range(3):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "ollama",
                "domain": "default",
            }
        )
        time.sleep(0.01)  # Very fast

    assert len(threshold_events) == 1
    # Velocity should be 3 (3 failures in < 1 second)
    assert threshold_events[0]["failure_velocity"] >= 3


def test_counter_resets_after_threshold():
    """Test that counter resets after hitting threshold."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Hit threshold (3 failures)
    for i in range(3):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "default",
            }
        )

    assert len(threshold_events) == 1

    # Two more failures shouldn't trigger again (counter reset)
    for i in range(2):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "Filesystem",
                "domain": "default",
            }
        )

    # Still only 1 threshold event
    assert len(threshold_events) == 1

    # One more should trigger again (3 total since reset)
    bus.emit(
        {
            "event": "tool_call_failed",
            "tool_family": "Filesystem",
            "domain": "default",
        }
    )

    assert len(threshold_events) == 2


def test_fallback_threshold():
    """Test fallback threshold for unconfigured families."""
    bus = EventBus()
    config = get_test_config()
    tracker = FailureTracker(bus, config)

    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))

    # Use unconfigured family - should use fallback threshold of 3
    for i in range(3):
        bus.emit(
            {
                "event": "tool_call_failed",
                "tool_family": "UnknownFamily",
                "domain": "default",
            }
        )

    assert len(threshold_events) == 1
    assert threshold_events[0]["threshold"] == 3
