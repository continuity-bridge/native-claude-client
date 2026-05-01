# Event System Architecture

**Version:** 1.0.0  
**Status:** Design Specification  
**Author:** Vector/Shepard + Uncle Tallest  
**Created:** 2026-04-01

---

## Executive Summary

The Event System is the **foundational infrastructure** for Erebos's hook-based automation. It provides a centralized event bus that emits lifecycle events, enabling instance behavior automation without manual intervention.

**Core Purpose:** Make critical instance behaviors unavoidable by triggering them automatically at the right moments.

**Dependencies:** None - this is Phase 2, the foundation everything else builds on.

**Enables:**
- Predictive tool loading on session start
- Auto tool loading on consecutive failures
- Session capture before context loss
- Proactive context compaction
- Decision logging and validation
- All hook-based automation

---

## Architecture Overview

### Event Flow

```
Session Start
    ↓
Event Emitter → Event Bus → Hook Registry → Hook Executors → Actions
    ↑
Tool Failure / Token Threshold / User Action
```

**Components:**

1. **Event Emitter** - Detects conditions, emits events
2. **Event Bus** - Central routing, pub/sub pattern
3. **Hook Registry** - Maps events to hooks (reads hooks-registry.json)
4. **Hook Executors** - Markdown files with execution logic
5. **Actions** - tool_search calls, file writes, API calls

---

## Core Events

### 1. session_start

**When:** New conversation begins OR app launch with no prior session

**Payload:**
```python
{
    "event": "session_start",
    "timestamp": "2026-04-01T14:30:00Z",
    "session_id": "uuid-v4",
    "platform": "Erebos",
    "domain": "domain_1_professional",  # detected from context
    "prior_session_id": "uuid-v4" | None  # if resuming
}
```

**Triggers:**
- predictive-tool-loader hook
- domain detection logic
- session metadata creation

---

### 2. tool_call_failed

**When:** Any tool call returns error or "not loaded" message

**Payload:**
```python
{
    "event": "tool_call_failed",
    "timestamp": "2026-04-01T14:32:15Z",
    "session_id": "uuid-v4",
    "tool_name": "Filesystem:read_file",
    "tool_family": "Filesystem",  # mapped from config
    "error_type": "not_loaded" | "timeout" | "api_error",
    "error_message": "Tool has not been loaded yet",
    "consecutive_failures": 1,  # for this family
    "failure_velocity": 0.0  # failures per minute
}
```

**Triggers:**
- Auto tool loader (when threshold reached)
- Failure tracking updates
- Usage analytics logging

---

### 3. failure_threshold

**When:** Consecutive tool failures reach configured threshold

**Payload:**
```python
{
    "event": "failure_threshold",
    "timestamp": "2026-04-01T14:32:45Z",
    "session_id": "uuid-v4",
    "tool_family": "Filesystem",
    "consecutive_failures": 3,
    "threshold": 3,
    "failure_velocity": 45.0,  # failures/min
    "velocity_adjusted_threshold": 1.5,  # threshold * 0.5 if velocity high
    "domain": "domain_1_professional"
}
```

**Triggers:**
- auto-tool-loader hook (immediate execution)

---

### 4. token_threshold

**When:** Token usage crosses configured percentages

**Payload:**
```python
{
    "event": "token_threshold",
    "timestamp": "2026-04-01T14:45:00Z",
    "session_id": "uuid-v4",
    "current_tokens": 120000,
    "max_tokens": 200000,
    "percentage": 60.0,
    "threshold_crossed": 60,  # can be 60, 80, 85, 90
    "messages_count": 45
}
```

**Triggers:**
- auto-compact hook (at 60%)
- session-end hook (at 85%+)

---

### 5. session_end

**When:** User signals end OR natural conversation close

**Payload:**
```python
{
    "event": "session_end",
    "timestamp": "2026-04-01T15:00:00Z",
    "session_id": "uuid-v4",
    "trigger": "user_keyword" | "inactivity" | "app_close",
    "duration_seconds": 1800,
    "messages_count": 52,
    "token_usage": 145000,
    "files_created": ["/path/to/file1.md", "/path/to/file2.py"],
    "tool_families_used": ["Filesystem", "Notion", "GoogleCalendar"]
}
```

**Triggers:**
- session-end hook (write to Notion + local + Drive)
- tool-usage-analyzer hook

---

### 6. work_unit_completed

**When:** Git commit, phase wrap, or deliverable finished

**Payload:**
```python
{
    "event": "work_unit_completed",
    "timestamp": "2026-04-01T14:50:00Z",
    "session_id": "uuid-v4",
    "unit_type": "git_commit" | "phase_wrap" | "deliverable",
    "commit_hash": "abc123" | None,
    "files_modified": ["/path/to/file.py"],
    "description": "Add event system architecture"
}
```

**Triggers:**
- auto-compact hook (proactive rotation)

---

## Implementation Components

### Component 1: Event Emitter

**Location:** `erebos/events/emitter.py`

**Responsibilities:**
- Detect conditions that warrant events
- Construct event payloads
- Emit to event bus
- No business logic (just detection + emission)

**Key Methods:**
```python
class EventEmitter:
    def __init__(self, event_bus):
        self.bus = event_bus
        self.session_id = None
    
    def start_session(self, domain=None):
        """Emit session_start event"""
        self.session_id = str(uuid.uuid4())
        self.bus.emit({
            "event": "session_start",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": self.session_id,
            "domain": domain or "default"
        })
    
    def tool_failed(self, tool_name, error):
        """Emit tool_call_failed event"""
        # Detect tool family
        # Track consecutive failures
        # Calculate velocity
        # Emit event
    
    def check_token_threshold(self, current, max_tokens):
        """Emit token_threshold if crossed"""
        percentage = (current / max_tokens) * 100
        for threshold in [60, 80, 85, 90]:
            if percentage >= threshold and not self._crossed[threshold]:
                self.bus.emit({...})
                self._crossed[threshold] = True
```

---

### Component 2: Event Bus

**Location:** `erebos/events/bus.py`

**Responsibilities:**
- Central event routing
- Pub/sub pattern
- Deliver events to all subscribers
- Event logging

**Key Methods:**
```python
class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)  # event_type -> [handlers]
        self.logger = EventLogger()
    
    def subscribe(self, event_type, handler):
        """Register handler for event type"""
        self.subscribers[event_type].append(handler)
    
    def emit(self, event):
        """Publish event to all subscribers"""
        event_type = event.get("event")
        self.logger.log(event)
        
        for handler in self.subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                # Log error, don't crash
                pass
```

---

### Component 3: Tool Failure Tracker

**Location:** `erebos/events/failure_tracker.py`

**Responsibilities:**
- Count consecutive failures per tool family
- Calculate failure velocity (failures/minute)
- Detect when threshold reached
- Emit failure_threshold events

**Key Data Structures:**
```python
class FailureTracker:
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config  # hooks-config.json
        self.failures = {}  # family -> count
        self.failure_times = {}  # family -> [timestamps]
        self.last_success = {}  # family -> timestamp
    
    def on_tool_failed(self, event):
        """Track failure, emit threshold event if needed"""
        family = event["tool_family"]
        
        # Reset if last call succeeded
        if family in self.last_success:
            self.failures[family] = 0
        
        # Increment
        self.failures[family] = self.failures.get(family, 0) + 1
        
        # Track timing
        now = time.time()
        if family not in self.failure_times:
            self.failure_times[family] = []
        self.failure_times[family].append(now)
        
        # Calculate velocity (failures in last 60s)
        recent = [t for t in self.failure_times[family] if now - t < 60]
        velocity = len(recent)  # per minute
        
        # Get threshold
        threshold = self._get_threshold(family, event["domain"])
        
        # Velocity adjustment
        if velocity >= 10:
            threshold = max(1, int(threshold * 0.5))
        
        # Check threshold
        if self.failures[family] >= threshold:
            self.bus.emit({
                "event": "failure_threshold",
                "tool_family": family,
                "consecutive_failures": self.failures[family],
                "threshold": threshold,
                "failure_velocity": velocity,
                ...
            })
    
    def _get_threshold(self, family, domain):
        """Get threshold from config"""
        # Check domain-specific override
        # Fall back to default
        # Return threshold value
```

---

### Component 4: Token Monitor

**Location:** `erebos/events/token_monitor.py`

**Responsibilities:**
- Track current token usage
- Detect threshold crossings (60%, 80%, 85%, 90%)
- Emit token_threshold events
- Prevent duplicate emissions per threshold

**Key Methods:**
```python
class TokenMonitor:
    def __init__(self, event_bus, max_tokens=200000):
        self.bus = event_bus
        self.max_tokens = max_tokens
        self.current_tokens = 0
        self.crossed = {60: False, 80: False, 85: False, 90: False}
    
    def update(self, token_count):
        """Update token count, emit if threshold crossed"""
        self.current_tokens = token_count
        percentage = (token_count / self.max_tokens) * 100
        
        for threshold in [60, 80, 85, 90]:
            if percentage >= threshold and not self.crossed[threshold]:
                self.bus.emit({
                    "event": "token_threshold",
                    "current_tokens": token_count,
                    "max_tokens": self.max_tokens,
                    "percentage": percentage,
                    "threshold_crossed": threshold,
                    ...
                })
                self.crossed[threshold] = True
```

---

### Component 5: Hook Executor Engine

**Location:** `erebos/hooks/executor.py`

**Responsibilities:**
- Load hooks-registry.json + hooks-config.json
- Subscribe to events
- Execute hook logic when events fire
- Log hook executions

**Key Methods:**
```python
class HookExecutor:
    def __init__(self, event_bus):
        self.bus = event_bus
        self.registry = self._load_registry()
        self.config = self._load_config()
        self._subscribe_hooks()
    
    def _subscribe_hooks(self):
        """Subscribe enabled hooks to their trigger events"""
        for hook in self.registry["hooks"]:
            if hook["id"] in self.config["enabled_hooks"]:
                trigger_type = hook["trigger"]["type"]
                self.bus.subscribe(trigger_type, 
                    lambda event: self._execute_hook(hook, event))
    
    def _execute_hook(self, hook, event):
        """Execute hook logic"""
        # Check if conditions met
        if not self._conditions_met(hook, event):
            return
        
        # Load executor markdown
        executor_path = hook["executor"]
        # Parse executor instructions
        # Execute steps
        # Log to JSONL
        
        self._log_execution(hook["id"], event, success=True)
```

---

## File Structure

```
erebos/
├── events/
│   ├── __init__.py
│   ├── emitter.py           # EventEmitter class
│   ├── bus.py               # EventBus class
│   ├── failure_tracker.py   # FailureTracker class
│   └── token_monitor.py     # TokenMonitor class
│
├── hooks/
│   ├── __init__.py
│   ├── executor.py          # HookExecutor class
│   └── logger.py            # Hook execution logging
│
├── session/
│   ├── __init__.py
│   └── manager.py           # SessionManager (orchestrates events)
│
└── config/
    ├── hooks-registry.json  # Symlink to Substrate hooks
    └── hooks-config.json    # Symlink to Substrate hooks
```

---

## Integration Points

### With Claude API Client

```python
# In API client code
class ClaudeClient:
    def __init__(self):
        self.event_bus = EventBus()
        self.emitter = EventEmitter(self.event_bus)
        self.failure_tracker = FailureTracker(self.event_bus, config)
        self.token_monitor = TokenMonitor(self.event_bus)
        self.hook_executor = HookExecutor(self.event_bus)
        
        # Subscribe failure tracker to tool_call_failed
        self.event_bus.subscribe("tool_call_failed", 
            self.failure_tracker.on_tool_failed)
    
    def start_conversation(self, domain=None):
        """Start new conversation"""
        self.emitter.start_session(domain)
        # Hooks are automatically triggered by session_start event
    
    def call_tool(self, tool_name, params):
        """Call a tool, emit events on failure"""
        try:
            result = self._execute_tool(tool_name, params)
            return result
        except ToolNotLoadedError as e:
            self.emitter.tool_failed(tool_name, e)
            raise
    
    def send_message(self, message):
        """Send message, update token count"""
        response = self.api.send(message)
        self.token_monitor.update(response.usage.total_tokens)
        return response
```

---

## Event Logging

**Location:** `logs/hooks/hook-execution.jsonl`

**Format:** One JSON object per line (JSONL)

**Schema:**
```json
{
  "timestamp": "2026-04-01T14:30:00Z",
  "session_id": "uuid-v4",
  "event_type": "session_start",
  "hook_id": "predictive-tool-loader",
  "hook_name": "PredictiveToolLoader",
  "trigger_conditions": ["new_session: true"],
  "execution_status": "success" | "failed" | "skipped",
  "execution_time_ms": 245,
  "actions_taken": ["tool_search: filesystem", "tool_search: calendar"],
  "error_message": null | "Error description"
}
```

**Query Examples:**
```bash
# Count hook executions by type
jq '.hook_id' logs/hooks/hook-execution.jsonl | sort | uniq -c

# Failed hook executions
jq 'select(.execution_status=="failed")' logs/hooks/hook-execution.jsonl

# Average execution time per hook
jq -r 'select(.hook_id=="predictive-tool-loader") | .execution_time_ms' \
  logs/hooks/hook-execution.jsonl | \
  awk '{sum+=$1; count++} END {print sum/count}'
```

---

## Testing Strategy

### Unit Tests

**Test Event Emitter:**
```python
def test_session_start_emission():
    bus = EventBus()
    emitter = EventEmitter(bus)
    events = []
    bus.subscribe("session_start", lambda e: events.append(e))
    
    emitter.start_session(domain="domain_1_professional")
    
    assert len(events) == 1
    assert events[0]["event"] == "session_start"
    assert events[0]["domain"] == "domain_1_professional"
```

**Test Failure Tracker:**
```python
def test_threshold_detection():
    bus = EventBus()
    tracker = FailureTracker(bus, config)
    threshold_events = []
    bus.subscribe("failure_threshold", 
        lambda e: threshold_events.append(e))
    
    # Simulate 3 consecutive failures
    for i in range(3):
        tracker.on_tool_failed({
            "tool_family": "Filesystem",
            "domain": "default"
        })
    
    assert len(threshold_events) == 1
    assert threshold_events[0]["tool_family"] == "Filesystem"
```

### Integration Tests

**Test Hook Execution:**
```python
def test_hook_triggers_on_event():
    bus = EventBus()
    executor = HookExecutor(bus)
    
    # Mock hook registry with test hook
    # Emit event that should trigger hook
    # Verify hook execution logged
```

---

## Performance Considerations

**Event Bus Overhead:**
- Events are in-memory, no network calls
- Subscribers execute synchronously (fast)
- Estimated overhead: <1ms per event

**Failure Tracking:**
- O(1) lookup and update
- Sliding window (last 60s) kept pruned
- Memory: <1KB per tool family

**Token Monitoring:**
- Simple arithmetic comparison
- No state persistence required
- Negligible overhead

**Hook Execution:**
- Executor markdown parsing: ~10-50ms
- Tool calls (e.g., tool_search): 2-5s
- File operations: <100ms

**Total System Impact:** <0.1% CPU, <10MB RAM

---

## Security & Privacy

**Event Data:**
- Events contain no user message content
- Tool parameters not logged (may contain sensitive data)
- Session IDs are UUIDs (not traceable to user)

**Hook Executors:**
- Cannot make arbitrary network calls
- Filesystem access limited to Substrate directory
- API keys only for Anthropic/Notion (user-configured)

**Logging:**
- JSONL logs stay local (not uploaded)
- User can disable logging via config
- No PII in event payloads

---

## Migration Path (v0.1 → v0.2)

**v0.1 MVP:**
- Event system implemented
- Core events (session_start, tool_call_failed, token_threshold)
- Basic hook executor
- predictive-tool-loader + auto-tool-loader

**v0.2 Multi-Session:**
- session_start per tab/pane
- Cross-session failure tracking
- Per-session token monitoring
- Shared event bus across sessions

---

## Success Metrics

**Phase 2 Complete When:**
- ✅ Event bus emitting all 6 core events
- ✅ Failure tracker detecting thresholds
- ✅ Token monitor emitting at 60%, 80%, 85%, 90%
- ✅ Hook executor loading registry + config
- ✅ predictive-tool-loader firing on session_start
- ✅ auto-tool-loader firing on failure_threshold
- ✅ All events logged to JSONL

**Validation Tests:**
- [ ] Start session → session_start emitted
- [ ] 3 tool failures → failure_threshold emitted
- [ ] 60% tokens → token_threshold emitted
- [ ] Hooks execute within 5s of trigger
- [ ] JSONL logs parseable and queryable

---

## Next Steps

**Week 1-2:**
1. Implement EventBus + EventEmitter
2. Add unit tests
3. Integrate with Claude API client stub

**Week 3:**
4. Implement FailureTracker
5. Implement TokenMonitor
6. Add integration tests

**Week 4:**
7. Implement HookExecutor
8. Load hooks from Substrate symlinks
9. Test end-to-end flow

**Week 5-6:**
10. Polish error handling
11. Add logging
12. Performance testing
13. Documentation

---

**Version:** 1.0.0  
**Created:** 2026-04-01  
**Next Review:** After Phase 2 implementation

---

*The foundation upon which all automation stands.*
