#!/usr/bin/env python3
"""
Prototype CLI for testing event system with Ollama.

This demonstrates the event-driven architecture before building the GTK4 UI.
"""

import logging
from erebos.events.bus import EventBus
from erebos.events.emitter import EventEmitter
from erebos.llm.ollama_client import OllamaClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    """Run prototype event system test."""
    print("=" * 60)
    print("Native Claude Client - Event System Prototype")
    print("=" * 60)
    print()
    
    # Set up event system
    bus = EventBus()
    emitter = EventEmitter(bus)
    
    # Subscribe to events for debugging
    bus.subscribe("session_start", 
                 lambda e: print(f"✓ Session started: {e['session_id'][:8]}... (domain: {e['domain']})"))
    bus.subscribe("session_end", 
                 lambda e: print(f"✓ Session ended: {e['duration_seconds']:.1f}s"))
    bus.subscribe("tool_call_failed", 
                 lambda e: print(f"✗ Tool failed: {e['tool_name']} ({e['error_type']})"))
    bus.subscribe("tool_call_success", 
                 lambda e: print(f"✓ Tool succeeded: {e['tool_name']}"))
    
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
    print("--- Starting Test Session ---")
    emitter.start_session(domain="prototype")
    print()
    
    # Test 1: Normal successful call
    print("Test 1: Normal chat call")
    try:
        response = client.chat(models[0], "Say hello in exactly 5 words.")
        print(f"  Response: \"{response.strip()}\"")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 2: Non-existent model (failure)
    print("Test 2: Intentional failure (non-existent model)")
    try:
        client.chat("nonexistent-model-xyz", "test")
    except Exception as e:
        print(f"  Expected error: {e}")
    print()
    
    # Test 3: Multiple calls to test event counting
    print("Test 3: Rapid fire calls (3x)")
    for i in range(3):
        try:
            response = client.chat(models[0], f"Count to {i+1}")
            print(f"  Call {i+1}: Success ({len(response)} chars)")
        except Exception as e:
            print(f"  Call {i+1}: Failed")
    print()
    
    # End session
    print("--- Ending Test Session ---")
    emitter.end_session("test_complete")
    print()
    
    # Stats
    print(f"Total events emitted: {bus.event_count}")
    print()
    print("=" * 60)
    print("Event system validated ✓")
    print("Next step: Add FailureTracker to monitor consecutive failures")
    print("=" * 60)


if __name__ == "__main__":
    main()
