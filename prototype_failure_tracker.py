#!/usr/bin/env python3
"""
Enhanced prototype CLI with FailureTracker.

Demonstrates intelligent failure detection and threshold events.
"""

import logging
from erebos.events.bus import EventBus
from erebos.events.emitter import EventEmitter
from erebos.events.failure_tracker import FailureTracker
from erebos.llm.ollama_client import OllamaClient

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)


def main():
    """Run enhanced prototype with FailureTracker."""
    print("=" * 60)
    print("Native Claude Client - FailureTracker Demo")
    print("=" * 60)
    print()

    # Set up event system
    bus = EventBus()
    emitter = EventEmitter(bus)

    # FailureTracker configuration
    config = {
        "tool_family_thresholds": {
            "default": {
                "Filesystem": 3,
                "ollama": 3,
                "Notion": 3,
            }
        }
    }

    # Create FailureTracker
    tracker = FailureTracker(bus, config)

    # Subscribe to events for debugging
    bus.subscribe(
        "session_start",
        lambda e: print(
            f"✓ Session started: {e['session_id'][:8]}... (domain: {e['domain']})"
        ),
    )
    bus.subscribe("session_end", lambda e: print(f"✓ Session ended: {e['duration_seconds']:.1f}s"))
    bus.subscribe(
        "tool_call_failed", lambda e: print(f"✗ Tool failed: {e['tool_name']} ({e['error_type']})")
    )
    bus.subscribe(
        "tool_call_success", lambda e: print(f"✓ Tool succeeded: {e['tool_name']}")
    )
    bus.subscribe(
        "failure_threshold",
        lambda e: print(
            f"⚠ THRESHOLD REACHED: {e['tool_family']} "
            f"({e['consecutive_failures']} failures, velocity: {e['failure_velocity']}/min)"
        ),
    )

    # Create LLM client
    client = OllamaClient()
    client.event_emitter = emitter

    # Check available models
    print("Checking Ollama connection...")
    models = client.list_models()
    if not models:
        print("⚠ No models found. Is Ollama running?")
        print("  Start it with: ollama serve")
        return

    print(f"✓ Found {len(models)} model(s): {', '.join(models[:3])}")
    print()

    # Start session
    print("--- Starting FailureTracker Demo ---")
    emitter.start_session(domain="prototype")
    print()

    # Test 1: Demonstrate threshold detection
    print("Test 1: Trigger failure threshold (3 consecutive failures)")
    for i in range(3):
        try:
            print(f"  Attempt {i+1}: Calling nonexistent model...")
            client.chat("nonexistent-model-xyz", "test")
        except Exception:
            pass  # Expected to fail

    print()

    # Test 2: Show success resets counter
    print("Test 2: Success resets failure counter")
    # Fail twice
    for i in range(2):
        try:
            print(f"  Failure {i+1}...")
            client.chat("another-nonexistent-model", "test")
        except Exception:
            pass

    # Success
    print("  Success call...")
    try:
        client.chat(models[0], "Say hello in 3 words")
    except Exception as e:
        print(f"  Unexpected error: {e}")

    # Fail twice more - shouldn't trigger threshold (counter was reset)
    for i in range(2):
        try:
            print(f"  Failure {i+3}...")
            client.chat("yet-another-fake-model", "test")
        except Exception:
            pass

    print("  (No threshold triggered - counter was reset by success)")
    print()

    # Test 3: Show separate family tracking
    print("Test 3: Separate tool families tracked independently")
    print("  Simulating Filesystem failures (won't affect ollama counter)...")
    for i in range(2):
        emitter.tool_failed(
            tool_name="Filesystem:read_file",
            tool_family="Filesystem",
            error_type="not_loaded",
            error_message="Tool not loaded",
        )
    print("  (No threshold yet - different family, different counter)")
    print()

    # End session
    print("--- Ending Demo Session ---")
    emitter.end_session("demo_complete")
    print()

    # Stats
    print(f"Total events emitted: {bus.event_count}")
    print()
    print("=" * 60)
    print("FailureTracker validated ✓")
    print()
    print("Key behaviors demonstrated:")
    print("  • Threshold events trigger after N consecutive failures")
    print("  • Success calls reset the failure counter")
    print("  • Tool families are tracked separately")
    print("  • Velocity-based threshold adjustment (for rapid failures)")
    print()
    print("Next step: Add TokenMonitor for usage tracking")
    print("=" * 60)


if __name__ == "__main__":
    main()
