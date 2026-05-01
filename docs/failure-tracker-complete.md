# FailureTracker Implementation Complete

**Date:** 2026-04-18  
**Status:** ✓ Implemented and tested

## What Was Built

FailureTracker is the intelligent monitoring layer that detects when tool calls are failing repeatedly and emits threshold events. This enables the native client to automatically respond to patterns of failure (e.g., auto-loading tools that haven't been loaded yet).

### Core Features

1. **Consecutive Failure Tracking**
   - Monitors failures per tool family (Filesystem, Notion, ollama, etc.)
   - Maintains separate counters for each family
   - Emits `failure_threshold` event when threshold reached

2. **Success-Based Reset**
   - Success calls reset the failure counter for that family
   - Prevents false positives from intermittent failures

3. **Domain-Specific Thresholds**
   - Different domains can have different sensitivity
   - Example: Professional domain might be more aggressive (threshold=2)
   - Falls back to default threshold (3) if not configured

4. **Velocity Detection**
   - Calculates failure rate (failures per minute)
   - Adjusts threshold downward for rapid failures (high velocity)
   - Example: 10+ failures/min → threshold halved

## Files Created

```
erebos/events/
└── failure_tracker.py         # FailureTracker implementation (120 lines)

tests/events/
├── test_config.py             # Test configuration
└── test_failure_tracker.py    # Unit tests (8 test cases)

tests/integration/
└── test_failure_tracking.py   # Integration tests (3 scenarios)

prototype_failure_tracker.py   # Interactive demo
```

## Test Coverage

**8 unit tests:**
- ✓ Threshold detection after N failures
- ✓ Success resets counter
- ✓ Domain-specific thresholds
- ✓ Separate family tracking
- ✓ Velocity calculation
- ✓ Counter resets after threshold
- ✓ Fallback threshold for unconfigured families

**3 integration tests:**
- ✓ Full integration with EventBus and EventEmitter
- ✓ Real Ollama client failure tracking
- ✓ Mixed success/failure patterns

## Configuration Format

```python
config = {
    "tool_family_thresholds": {
        "default": {
            "Filesystem": 3,
            "Notion": 3,
            "ollama": 3,
        },
        "domain_1_professional": {
            "Filesystem": 2,  # Lower threshold = more aggressive
            "Notion": 4,       # Higher threshold = more lenient
        }
    }
}
```

## Event Schema

**Input Events** (subscribed):
- `tool_call_failed` - Increments counter
- `tool_call_success` - Resets counter

**Output Event** (emitted):
```python
{
    "event": "failure_threshold",
    "timestamp": "2026-04-18T23:15:42Z",
    "tool_family": "Filesystem",
    "consecutive_failures": 3,
    "threshold": 3,
    "failure_velocity": 5,  # failures per minute
    "velocity_adjusted_threshold": 2,  # adjusted for high velocity
    "domain": "default"
}
```

## Usage Example

```python
from erebos.events.bus import EventBus
from erebos.events.emitter import EventEmitter
from erebos.events.failure_tracker import FailureTracker

# Set up
bus = EventBus()
emitter = EventEmitter(bus)
config = {"tool_family_thresholds": {"default": {"Filesystem": 3}}}
tracker = FailureTracker(bus, config)

# Subscribe to threshold events
bus.subscribe("failure_threshold", lambda e: print(f"Threshold hit: {e['tool_family']}"))

# Simulate failures
emitter.start_session()
for i in range(3):
    emitter.tool_failed("Filesystem:read_file", "Filesystem", "not_loaded", "Error")

# Threshold event fires after 3rd failure
```

## Running the Demo

```bash
python prototype_failure_tracker.py
```

**Sample Output:**
```
============================================================
Native Claude Client - FailureTracker Demo
============================================================

Test 1: Trigger failure threshold (3 consecutive failures)
  Attempt 1: Calling nonexistent model...
✗ Tool failed: ollama:nonexistent-model-xyz (api_error)
  Attempt 2: Calling nonexistent model...
✗ Tool failed: ollama:nonexistent-model-xyz (api_error)
  Attempt 3: Calling nonexistent model...
✗ Tool failed: ollama:nonexistent-model-xyz (api_error)
⚠ THRESHOLD REACHED: ollama (3 failures, velocity: 3/min)
```

## Next Steps

1. **Add TokenMonitor** - Track token usage and emit at percentage thresholds
2. **Add HookExecutor** - Load hooks and execute on events
3. **Test end-to-end** - Validate complete event → hook → action workflow

## Design Notes

**Why separate tracking per family?**
- Different tools have different failure patterns
- Filesystem errors shouldn't trigger Notion auto-loading
- Enables targeted responses (e.g., load specific tool family)

**Why velocity adjustment?**
- Rapid failures indicate urgent problem
- Lower threshold = faster response
- Prevents runaway failure loops

**Why reset on success?**
- Intermittent failures are normal
- Only *consecutive* failures indicate pattern
- Success proves the issue was temporary

---

**Implemented:** 2026-04-18 23:15 UTC  
**By:** Vector (with Uncle Tallest)  
**Test Status:** All tests passing ✓
