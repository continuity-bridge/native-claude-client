"""
Unit tests for EventBus.
"""

import pytest
from erebos.events.bus import EventBus


def test_subscribe_and_emit():
    """Test basic subscribe and emit flow."""
    bus = EventBus()
    events_received = []

    bus.subscribe("test_event", lambda e: events_received.append(e))
    bus.emit({"event": "test_event", "data": "hello"})

    assert len(events_received) == 1
    assert events_received[0]["data"] == "hello"


def test_multiple_subscribers():
    """Test multiple handlers for same event."""
    bus = EventBus()
    count_a = [0]
    count_b = [0]

    bus.subscribe("test", lambda e: count_a.__setitem__(0, count_a[0] + 1))
    bus.subscribe("test", lambda e: count_b.__setitem__(0, count_b[0] + 1))

    bus.emit({"event": "test"})

    assert count_a[0] == 1
    assert count_b[0] == 1


def test_handler_error_doesnt_crash():
    """Test that one handler failing doesn't stop others."""
    bus = EventBus()
    results = []

    bus.subscribe("test", lambda e: 1 / 0)  # Will raise ZeroDivisionError
    bus.subscribe("test", lambda e: results.append("success"))

    bus.emit({"event": "test"})

    assert "success" in results  # Second handler still ran


def test_event_count():
    """Test that event_count tracks emissions."""
    bus = EventBus()

    assert bus.event_count == 0

    bus.emit({"event": "test1"})
    assert bus.event_count == 1

    bus.emit({"event": "test2"})
    assert bus.event_count == 2


def test_clear_all():
    """Test clearing all subscribers."""
    bus = EventBus()
    events = []

    bus.subscribe("test", lambda e: events.append(e))
    bus.emit({"event": "test"})

    assert len(events) == 1

    bus.clear_all()

    # Counter should be reset immediately after clear_all
    assert bus.event_count == 0

    # Emit after clearing - no handlers should run
    bus.emit({"event": "test"})

    # Still only 1 event in list because handler was cleared
    assert len(events) == 1
    # Counter incremented by the emit call
    assert bus.event_count == 1
