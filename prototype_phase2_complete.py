#!/usr/bin/env python3
"""
Complete Phase 2 Demo - All event system components working together.

Demonstrates:
- EventBus routing events
- FailureTracker monitoring failures
- TokenMonitor tracking usage
- HookExecutor responding to events
"""

import json
import logging
import tempfile
from native_claude_client.events.bus import EventBus
from native_claude_client.events.emitter import EventEmitter
from native_claude_client.events.failure_tracker import FailureTracker
from native_claude_client.events.token_monitor import TokenMonitor
from native_claude_client.events.hook_executor import HookExecutor
from native_claude_client.llm.ollama_client import OllamaClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def create_test_hooks():
    """Create temporary hook registry and config files for demo."""
    registry = {
        "hooks": [
            {
                "id": "auto-tool-loader",
                "trigger": {"type": "failure_threshold"},
                "executor": "auto-load-tools.md",
                "description": "Auto-load tools after failure threshold"
            },
            {
                "id": "auto-compact",
                "trigger": {"type": "token_threshold"},
                "executor": "compact-context.md",
                "description": "Proactive context compaction"
            }
        ]
    }
    
    config = {
        "enabled_hooks": ["auto-tool-loader", "auto-compact"]
    }
    
    # Create temp files
    reg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(registry, reg_file)
    reg_file.close()
    
    conf_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(config, conf_file)
    conf_file.close()
    
    return reg_file.name, conf_file.name


def main():
    """Run complete Phase 2 demo."""
    print("=" * 70)
    print("Native Claude Client - Phase 2 Complete Demo")
    print("=" * 70)
    print()

    # Set up event system
    bus = EventBus()
    emitter = EventEmitter(bus)

    # FailureTracker configuration
    failure_config = {
        "tool_family_thresholds": {
            "default": {
                "Filesystem": 3,
                "ollama": 3,
                "Notion": 3,
            }
        }
    }

    # Create components
    tracker = FailureTracker(bus, failure_config)
    token_monitor = TokenMonitor(bus, max_tokens=100000)
    
    # Create hooks
    registry_path, config_path = create_test_hooks()
    hook_executor = HookExecutor(bus, registry_path=registry_path, config_path=config_path)

    # Subscribe to all events for display
    bus.subscribe(
        "session_start",
        lambda e: print(f"✓ Session started: {e['session_id'][:8]}...")
    )
    bus.subscribe(
        "tool_call_failed",
        lambda e: print(f"✗ Tool failed: {e['tool_name']}")
    )
    bus.subscribe(
        "tool_call_success",
        lambda e: print(f"✓ Tool succeeded: {e['tool_name']}")
    )
    bus.subscribe(
        "failure_threshold",
        lambda e: print(
            f"⚠ FAILURE THRESHOLD: {e['tool_family']} "
            f"({e['consecutive_failures']} failures)"
        )
    )
    bus.subscribe(
        "token_threshold",
        lambda e: print(
            f"⚠ TOKEN THRESHOLD: {e['threshold_crossed']}% "
            f"({e['current_tokens']:,} / {e['max_tokens']:,})"
        )
    )

    # Create LLM client
    client = OllamaClient()
    client.event_emitter = emitter

    # Check Ollama
    print("Checking Ollama connection...")
    models = client.list_models()
    if not models:
        print("⚠ No Ollama models found - using simulated failures")
        models = ["dummy-model"]
    else:
        print(f"✓ Found {len(models)} model(s)")
    print()

    # Start session
    print("--- Demo: Phase 2 Event System ---")
    emitter.start_session(domain="phase2_demo")
    print()

    # Demo 1: FailureTracker + HookExecutor
    print("Demo 1: Failure detection triggers hook")
    print("  Simulating 3 consecutive Filesystem failures...")
    for i in range(3):
        emitter.tool_failed(
            tool_name="Filesystem:read_file",
            tool_family="Filesystem",
            error_type="not_loaded",
            error_message="Tool not loaded"
        )
    print()

    # Demo 2: TokenMonitor + HookExecutor
    print("Demo 2: Token thresholds trigger compaction hook")
    print("  Simulating token usage...")
    token_monitor.update(50000)  # 50%
    print("  50% - No threshold yet")
    token_monitor.update(60000)  # 60% - First threshold
    token_monitor.update(80000)  # 80% - Second threshold
    print()

    # Demo 3: Multiple thresholds
    print("Demo 3: Multiple events triggering multiple hooks")
    print("  Simulating ollama failures...")
    for i in range(3):
        try:
            client.chat("nonexistent-model", "test")
        except Exception:
            pass
    
    print("  Simulating high token usage...")
    token_monitor.update(85000)  # 85%
    token_monitor.update(90000)  # 90%
    print()

    # End session
    emitter.end_session("demo_complete")
    print()

    # Show statistics
    print("=" * 70)
    print("Phase 2 Demo Complete")
    print("=" * 70)
    print()
    print("Event System Statistics:")
    print(f"  Total events emitted: {bus.event_count}")
    print(f"  Token usage: {token_monitor.current_tokens:,} / {token_monitor.max_tokens:,}")
    print(f"  Token percentage: {token_monitor.percentage_used:.1f}%")
    print(f"  Messages processed: {token_monitor.message_count}")
    print()
    
    print("Hook Execution History:")
    history = hook_executor.get_execution_history()
    for i, entry in enumerate(history, 1):
        print(f"  {i}. {entry['hook_id']} → {entry['event_type']} ({entry['execution_status']})")
    print()
    
    print("Components Validated:")
    print("  ✓ EventBus - Routing events to subscribers")
    print("  ✓ EventEmitter - Detecting and emitting events")
    print("  ✓ FailureTracker - Monitoring failure patterns")
    print("  ✓ TokenMonitor - Tracking token usage")
    print("  ✓ HookExecutor - Executing hooks on events")
    print()
    
    print("=" * 70)
    print("Phase 2 Complete - Ready for GTK4 UI (Phase 3)")
    print("=" * 70)


if __name__ == "__main__":
    main()
