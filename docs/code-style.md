# Code Style Guide

**For native-claude-client development**

This guide distills core coding principles for this project. Comprehensive style guides for all continuity-bridge projects will be published to the public repository.

---

## Core Principle: Elegant Code

**Definition:**
- **Readable at a glance** - No head-scratching required
- **Self-documenting** - Clear naming makes intent obvious
- **Minimally complex** - Simplest solution that works
- **Spatially organized** - Logical grouping, visual structure

**Anti-patterns:**
- Over-engineered solutions
- Clever tricks that sacrifice clarity
- Premature optimization
- Magic numbers or unexplained constants

**Guideline:** Code communicates intent to humans first, machines second.

---

## Python Conventions

**Target:** Python 3.11+ (available on all target platforms)

### Naming

```python
# Functions and variables: snake_case
def detect_platform():
    session_data = load_session()

# Classes: PascalCase
class SessionManager:
    pass

# Constants: SCREAMING_SNAKE_CASE
MAX_SESSIONS = 10
DEFAULT_TIMEOUT = 30

# Private members: _leading_underscore
class Widget:
    def __init__(self):
        self._internal_state = {}
```

### Type Hints

Encouraged but not required. Use when they add clarity:

```python
def process_conversation(
    messages: list[dict],
    context: str | None = None
) -> dict:
    """Process conversation history"""
    pass
```

### Docstrings

Keep concise but informative:

```python
def authenticate_session(token_path: str) -> bool:
    """
    Authenticate with Claude API using Desktop tokens.
    
    Args:
        token_path: Path to token file
        
    Returns:
        True if authentication succeeded
        
    Raises:
        FileNotFoundError: If token file doesn't exist
        AuthenticationError: If token is invalid/expired
    """
    pass
```

### Module Structure

```python
#!/usr/bin/env python3
"""Module docstring explaining purpose"""

# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

# Local imports
from .session import SessionManager
from .utils import load_config

# Constants
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Classes
class MainWindow(Gtk.ApplicationWindow):
    pass

# Functions
def main():
    pass

# Entry point
if __name__ == '__main__':
    main()
```

---

## Comments and Documentation

### Comments Explain WHY, Not HOW

**Good:**
```python
# Check if running in container (no SSH access in containers)
if Path('/home/claude').exists():
    use_clone_workflow = True
```

**Bad:**
```python
# Loop through sessions
for session in sessions:
    # Process each session
    process(session)
```

The code shows HOW. Comments provide context and reasoning.

### Attribution in Code

```python
#!/usr/bin/env python3
"""
Session management for native-claude-client

Author: Vector (AI-generated)
Created: 2026-03-09
Modified: 2026-08-15 by Jerry (added persistence)
"""
```

**Labels:**
- **Vector** or **Claude**: AI-generated contributions
- **Jerry** or **Uncle Tallest**: Human-written code
- **Collaborative**: Significant contributions from both

---

## Error Handling

### Use Specific Exceptions

```python
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    logger.error(f"Config not found: {config_path}")
    config = get_default_config()
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config: {e}")
    raise
```

**Avoid bare except:**

```python
# Bad
try:
    risky_operation()
except:
    pass

# Good
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    handle_error(e)
```

---

## GTK4 / PyGObject Conventions

### Widget Naming

```python
# Widgets: descriptive names with widget type
self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
self.input_entry = Gtk.Entry()
self.send_button = Gtk.Button(label="Send")
self.conversation_view = Gtk.TextView()
```

### Signal Connections

```python
# Clear, descriptive handler names
self.send_button.connect('clicked', self.on_send_clicked)
self.input_entry.connect('activate', self.on_input_activate)

def on_send_clicked(self, button):
    """Handle send button click"""
    message = self.input_entry.get_text()
    self.send_message(message)

def on_input_activate(self, entry):
    """Handle Enter key in input field"""
    self.on_send_clicked(None)  # Reuse send logic
```

---

## Code Organization

### Spatial Grouping

```python
# === Authentication ===

def load_token():
    pass

def validate_token():
    pass

# === Session Management ===

def create_session():
    pass

def save_session():
    pass

# === UI Rendering ===

def render_message():
    pass

def update_conversation():
    pass
```

Visual separation helps navigation.

### Function Length

**Guideline:** Functions do one thing well

- Generally keep under ~50 lines
- Exception: Linear workflows with clear steps
- If function gets long, decompose into helpers

```python
def initialize_session():
    """Main session initialization workflow"""
    token = load_authentication_token()
    api_client = create_api_client(token)
    session_state = restore_previous_session()
    ui = build_conversation_ui(session_state)
    return Session(api_client, session_state, ui)
```

Each helper has single, clear responsibility.

---

## File Paths

### Use pathlib

```python
from pathlib import Path

# Good - cross-platform
config_dir = Path.home() / '.config' / 'native-claude-client'
session_file = config_dir / 'sessions' / f'{session_id}.json'

# Bad - platform-specific
config_dir = "/home/user/.config/native-claude-client"  # Linux only
```

---

## Testing Checklist

Before committing:

- [ ] Code follows naming conventions
- [ ] Attribution is correct
- [ ] Comments explain WHY not HOW
- [ ] Error handling for likely failures
- [ ] Type hints where they add clarity
- [ ] Docstrings for public functions
- [ ] No hardcoded paths (use Path, config)
- [ ] Tested on target platform (Linux/GTK4)

---

## Quick Reference

| Element | Convention | Example |
|---------|-----------|---------|
| Functions/vars | snake_case | `detect_platform()` |
| Classes | PascalCase | `SessionManager` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |
| Private | _underscore | `_internal_cache` |
| Attribution | Vector/Jerry | `# Author: Vector` |
| Comments | WHY not HOW | `# Container has no SSH` |
| Exceptions | Specific | `except FileNotFoundError:` |
| Paths | pathlib | `Path.home() / '.config'` |
| GTK widgets | descriptive | `send_button` |

---

**Remember:** Readable code is maintainable code. When choosing between clever and clear, choose clear.

---

*This guide distills core principles for native-claude-client. Comprehensive style guides covering all continuity-bridge projects will be published to the public repository.*
