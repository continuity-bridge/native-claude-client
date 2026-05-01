# Phase 2 Implementation Guide

**Version:** 1.0.0  
**Target:** Erebos v0.1 MVP  
**Author:** Vector/Shepard + Uncle Tallest  
**Created:** 2026-04-01

---

## Overview

**Phase 2** builds the Event System - the foundation for all hook-based automation in Erebos. This guide provides step-by-step implementation instructions with code examples, test cases, and validation criteria.

**Timeline:** 6 weeks (44 hours estimated)  
**Dependencies:** None - this is foundational work  
**Blocks:** Phase 3 (Hooks), Phase 4 (Testing)

---

## Table of Contents

1. [Week 1-2: Event Infrastructure](#week-1-2-event-infrastructure)
2. [Week 3: Failure & Token Tracking](#week-3-failure--token-tracking)
3. [Week 4: Hook Executor Engine](#week-4-hook-executor-engine)
4. [Week 5-6: Integration & Polish](#week-5-6-integration--polish)
5. [Testing Strategy](#testing-strategy)
6. [Validation Checklist](#validation-checklist)

---

## Week 1-2: Event Infrastructure

**Goal:** Build EventBus, EventEmitter, and basic event flow  
**Estimated Time:** 20 hours

### Task 1.1: Create Project Structure (1h)

**Create directories:**
```bash
cd Erebos
mkdir -p erebos/events
mkdir -p erebos/hooks
mkdir -p erebos/session
mkdir -p logs/hooks
touch erebos/events/__init__.py
touch erebos/hooks/__init__.py
touch erebos/session/__init__.py
```

**Create symlinks to Substrate hooks:**
```bash
cd Erebos
ln -s ~/Substrate/.claude/FOUNDATION/hooks/hooks-registry.json \
  erebos/config/hooks-registry.json
ln -s ~/Substrate/.claude/FOUNDATION/hooks/hooks-config.json \
  erebos/config/hooks-config.json
```

---

### Task 1.2: Implement EventBus (4h)

**File:** `erebos/events/bus.py`

```python
"""
Event bus for pub/sub event routing.
Central hub for all events in Erebos.
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
        logger.debug(f"Subscribed handler to {event_type}, total handlers: {len(self.subscribers[event_type])}")
    
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
```

**Unit Tests:** `tests/events/test_bus.py`

```python
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
    
    bus.subscribe("test", lambda e: 1/0)  # Will raise ZeroDivisionError
    bus.subscribe("test", lambda e: results.append("success"))
    
    bus.emit({"event": "test"})
    
    assert "success" in results  # Second handler still ran
```

---

### Task 1.3: Implement EventEmitter (6h)

**File:** `erebos/events/emitter.py`

```python
"""
Event emitter for detecting conditions and publishing events.
"""

import uuid
from datetime import datetime
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
        self.session_start_time = datetime.utcnow()
        
        event = {
            "event": "session_start",
            "timestamp": self.session_start_time.isoformat() + "Z",
            "session_id": self.session_id,
            "platform": "Erebos",
            "domain": domain,
            "prior_session_id": prior_session_id
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
        
        duration = (datetime.utcnow() - self.session_start_time).total_seconds()
        
        event = {
            "event": "session_end",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "trigger": trigger,
            "duration_seconds": duration
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
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "tool_name": tool_name,
            "tool_family": tool_family,
            "error_type": error_type,
            "error_message": error_message
        }
        
        logger.warning(f"Tool {tool_name} failed: {error_type}")
        self.bus.emit(event)
    
    def work_unit_completed(self, unit_type: str, description: str, commit_hash: Optional[str] = None):
        """
        Emit work_unit_completed event.
        
        Args:
            unit_type: Type of work ("git_commit", "phase_wrap", "deliverable")
            description: Brief description
            commit_hash: Git commit hash if applicable
        """
        event = {
            "event": "work_unit_completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "unit_type": unit_type,
            "description": description,
            "commit_hash": commit_hash
        }
        
        logger.info(f"Work unit completed: {unit_type} - {description}")
        self.bus.emit(event)
```

**Unit Tests:** `tests/events/test_emitter.py`

```python
import pytest
from erebos.events.bus import EventBus
from erebos.events.emitter import EventEmitter


def test_session_start_emission():
    """Test session_start event emission."""
    bus = EventBus()
    emitter = EventEmitter(bus)
    events = []
    
    bus.subscribe("session_start", lambda e: events.append(e))
    emitter.start_session(domain="domain_1_professional")
    
    assert len(events) == 1
    assert events[0]["event"] == "session_start"
    assert events[0]["domain"] == "domain_1_professional"
    assert events[0]["session_id"] is not None


def test_tool_failed_emission():
    """Test tool_call_failed event emission."""
    bus = EventBus()
    emitter = EventEmitter(bus)
    emitter.session_id = "test-session"
    events = []
    
    bus.subscribe("tool_call_failed", lambda e: events.append(e))
    emitter.tool_failed(
        tool_name="Filesystem:read_file",
        tool_family="Filesystem",
        error_type="not_loaded",
        error_message="Tool has not been loaded yet"
    )
    
    assert len(events) == 1
    assert events[0]["tool_family"] == "Filesystem"
    assert events[0]["error_type"] == "not_loaded"
```

---

### Task 1.4: Integration Test (3h)

**Create end-to-end test:**

```python
# tests/integration/test_event_flow.py

def test_session_lifecycle():
    """Test complete session lifecycle with events."""
    bus = EventBus()
    emitter = EventEmitter(bus)
    
    # Track all events
    events = []
    bus.subscribe("session_start", lambda e: events.append(e))
    bus.subscribe("tool_call_failed", lambda e: events.append(e))
    bus.subscribe("session_end", lambda e: events.append(e))
    
    # Session flow
    emitter.start_session("domain_1_professional")
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "not_loaded", "Error")
    emitter.end_session("user_keyword")
    
    # Verify
    assert len(events) == 3
    assert events[0]["event"] == "session_start"
    assert events[1]["event"] == "tool_call_failed"
    assert events[2]["event"] == "session_end"
    assert events[0]["session_id"] == events[2]["session_id"]
```

---

### Task 1.5: Documentation (2h)

**Update README.md:**
- Add "Event System" section
- Link to event-system.md
- Show basic usage example

**Create developer guide:** `docs/events-dev-guide.md`
- How to emit custom events
- How to subscribe to events
- Event payload schemas
- Testing best practices

---

### Week 1-2 Deliverables

- [x] EventBus implemented with tests
- [x] EventEmitter implemented with tests
- [x] Integration tests passing
- [x] Documentation updated
- [x] Project structure established

---

## Week 3: Failure & Token Tracking

**Goal:** Implement FailureTracker and TokenMonitor  
**Estimated Time:** 12 hours

### Task 3.1: Implement FailureTracker (8h)

**File:** `erebos/events/failure_tracker.py`

```python
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
    
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config
        
        # State tracking
        self.failures: Dict[str, int] = defaultdict(int)  # family -> count
        self.failure_times: Dict[str, List[float]] = defaultdict(list)  # family -> [timestamps]
        self.last_success: Dict[str, float] = {}  # family -> timestamp
        
        # Subscribe to tool failures
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
        
        logger.debug(f"{family}: {self.failures[family]} failures (threshold: {adjusted_threshold}, velocity: {velocity}/min)")
        
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
        thresholds = self.config["auto-tool-loader"]["config"]["tool_family_thresholds"]
        
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
            "domain": domain
        }
        
        logger.warning(f"Failure threshold reached for {family}: {self.failures[family]} failures")
        self.bus.emit(event)
```

**Unit Tests:** `tests/events/test_failure_tracker.py`

```python
def test_threshold_detection():
    """Test that threshold event emits after N failures."""
    bus = EventBus()
    config = {
        "auto-tool-loader": {
            "config": {
                "tool_family_thresholds": {
                    "default": {"Filesystem": 3}
                }
            }
        }
    }
    tracker = FailureTracker(bus, config)
    
    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))
    
    # Simulate 3 consecutive failures
    for i in range(3):
        bus.emit({
            "event": "tool_call_failed",
            "tool_family": "Filesystem",
            "domain": "default"
        })
    
    assert len(threshold_events) == 1
    assert threshold_events[0]["tool_family"] == "Filesystem"
    assert threshold_events[0]["consecutive_failures"] == 3


def test_velocity_adjustment():
    """Test threshold reduction at high velocity."""
    bus = EventBus()
    config = {
        "auto-tool-loader": {
            "config": {
                "tool_family_thresholds": {
                    "default": {"Filesystem": 4}
                }
            }
        }
    }
    tracker = FailureTracker(bus, config)
    threshold_events = []
    bus.subscribe("failure_threshold", lambda e: threshold_events.append(e))
    
    # Rapid failures (15 in quick succession)
    for i in range(15):
        bus.emit({
            "event": "tool_call_failed",
            "tool_family": "Filesystem",
            "domain": "default"
        })
        time.sleep(0.01)  # Very fast
    
    # Should trigger before 4 due to velocity adjustment
    assert len(threshold_events) >= 1
```

---

### Task 3.2: Implement TokenMonitor (4h)

**File:** `erebos/events/token_monitor.py`

```python
"""
Monitors token usage and emits threshold crossing events.
"""

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
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "percentage": percentage,
            "threshold_crossed": threshold,
            "messages_count": self.message_count
        }
        
        logger.warning(f"Token threshold {threshold}% crossed ({self.current_tokens}/{self.max_tokens})")
        self.bus.emit(event)
    
    def reset(self):
        """Reset for new session."""
        self.current_tokens = 0
        self.message_count = 0
        self.crossed = {60: False, 80: False, 85: False, 90: False}
```

---

### Week 3 Deliverables

- [x] FailureTracker implemented with tests
- [x] TokenMonitor implemented with tests
- [x] Velocity-based threshold adjustment working
- [x] Domain-specific threshold config loading

---

## Week 4: Hook Executor Engine

**Goal:** Build hook executor that reads registry and executes hooks  
**Estimated Time:** 12 hours

### Task 4.1: Implement HookExecutor (12h)

**File:** `erebos/hooks/executor.py`

```python
"""
Hook executor engine - loads registry and executes hooks on events.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HookExecutor:
    """
    Loads hook registry and config, subscribes to events, executes hooks.
    """
    
    def __init__(self, event_bus, registry_path: str, config_path: str):
        self.bus = event_bus
        self.registry = self._load_json(registry_path)
        self.config = self._load_json(config_path)
        self.enabled_hooks = self.config.get("enabled_hooks", [])
        
        self._subscribe_hooks()
    
    def _load_json(self, path: str) -> Dict:
        """Load JSON file."""
        with open(path) as f:
            return json.load(f)
    
    def _subscribe_hooks(self):
        """Subscribe enabled hooks to their trigger events."""
        for hook in self.registry["hooks"]:
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
            # For now, just log that we would execute
            # In Phase 3, parse executor markdown and run steps
            logger.info(f"[STUB] Would execute: {hook['executor']}")
            
            # Log execution
            self._log_execution(hook_id, event, success=True)
            
        except Exception as e:
            logger.error(f"Hook '{hook_id}' execution failed: {e}", exc_info=True)
            self._log_execution(hook_id, event, success=False, error=str(e))
    
    def _conditions_met(self, hook: Dict, event: Dict) -> bool:
        """Check if hook conditions are satisfied."""
        conditions = hook["trigger"].get("conditions", [])
        
        # For now, assume conditions are met if event type matches
        # In Phase 3, implement full condition parsing
        return True
    
    def _log_execution(self, hook_id: str, event: Dict, success: bool, error: str = None):
        """Log hook execution to JSONL."""
        log_entry = {
            "timestamp": event.get("timestamp"),
            "session_id": event.get("session_id"),
            "event_type": event.get("event"),
            "hook_id": hook_id,
            "execution_status": "success" if success else "failed",
            "error_message": error
        }
        
        # Write to logs/hooks/hook-execution.jsonl
        log_path = Path("logs/hooks/hook-execution.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

---

### Week 4 Deliverables

- [x] HookExecutor loading registry + config
- [x] Hooks subscribing to events
- [x] Execution logging to JSONL
- [x] Condition checking (basic)
- [x] Phase 3 stub for executor parsing

---

## Week 5-6: Integration & Polish

**Remaining tasks - see full guide for details**

---

## Validation Checklist

**Phase 2 Complete When:**

- [ ] All unit tests passing (>95% coverage)
- [ ] Integration tests passing
- [ ] Event bus handling 1000+ events/sec
- [ ] Failure tracker correctly detecting thresholds
- [ ] Token monitor emitting at all percentages
- [ ] Hook executor loading registry
- [ ] JSONL logs parseable with jq
- [ ] Documentation complete
- [ ] Code review approved

---

**Version:** 1.0.0  
**Created:** 2026-04-01

---

*Build the foundation, everything else follows.*
