"""
Unit tests for TokenMonitor.
"""

import pytest
from erebos.events.bus import EventBus
from erebos.events.token_monitor import TokenMonitor


def test_threshold_emission_60():
    """Test 60% threshold emits event."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    threshold_events = []
    bus.subscribe("token_threshold", lambda e: threshold_events.append(e))

    # Update to 60% (60,000 tokens)
    monitor.update(60000)

    assert len(threshold_events) == 1
    assert threshold_events[0]["threshold_crossed"] == 60
    assert threshold_events[0]["percentage"] >= 60


def test_threshold_emission_80():
    """Test 80% threshold emits event."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    threshold_events = []
    bus.subscribe("token_threshold", lambda e: threshold_events.append(e))

    # Update to 80% (80,000 tokens)
    monitor.update(80000)

    # Should have emitted both 60% and 80%
    assert len(threshold_events) == 2
    assert threshold_events[0]["threshold_crossed"] == 60
    assert threshold_events[1]["threshold_crossed"] == 80


def test_all_thresholds():
    """Test all thresholds emit correctly."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    threshold_events = []
    bus.subscribe("token_threshold", lambda e: threshold_events.append(e))

    # Update to 95% (should trigger all 4 thresholds)
    monitor.update(95000)

    assert len(threshold_events) == 4
    thresholds = [e["threshold_crossed"] for e in threshold_events]
    assert thresholds == [60, 80, 85, 90]


def test_threshold_only_emits_once():
    """Test each threshold only emits once per session."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    threshold_events = []
    bus.subscribe("token_threshold", lambda e: threshold_events.append(e))

    # Hit 60% threshold
    monitor.update(60000)
    assert len(threshold_events) == 1

    # Update again to 65% - should not emit again
    monitor.update(65000)
    assert len(threshold_events) == 1  # Still only 1

    # Hit 80% threshold
    monitor.update(80000)
    assert len(threshold_events) == 2  # Now 2 (60% and 80%)


def test_reset():
    """Test reset clears all state."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    threshold_events = []
    bus.subscribe("token_threshold", lambda e: threshold_events.append(e))

    # Hit 60% threshold
    monitor.update(60000)
    assert len(threshold_events) == 1

    # Reset
    monitor.reset()

    assert monitor.current_tokens == 0
    assert monitor.message_count == 0
    assert monitor.percentage_used == 0

    # Hit 60% again - should emit (reset cleared the flag)
    monitor.update(60000)
    assert len(threshold_events) == 2


def test_message_count_increments():
    """Test message count increments on each update."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    assert monitor.message_count == 0

    monitor.update(1000)
    assert monitor.message_count == 1

    monitor.update(2000)
    assert monitor.message_count == 2

    monitor.update(3000)
    assert monitor.message_count == 3


def test_percentage_used_property():
    """Test percentage_used property calculates correctly."""
    bus = EventBus()
    monitor = TokenMonitor(bus, max_tokens=100000)

    monitor.update(50000)
    assert monitor.percentage_used == 50.0

    monitor.update(75000)
    assert monitor.percentage_used == 75.0

    monitor.update(90000)
    assert monitor.percentage_used == 90.0
