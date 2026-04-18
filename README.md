# native-claude-client

**Native GTK4 client for Claude with agentic development workflows and intelligent automation**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![GTK](https://img.shields.io/badge/GTK-4.0-orange.svg)](https://gtk.org)

---

## What is this?

A native Linux desktop application for Claude that goes beyond chat - it's an **agentic development environment** with intelligent automation:

- 🖥️ **Native GTK4/Wayland** - Truly native Linux UI, not Electron
- 🤖 **Hook System** - Event-driven automation for tool loading, session persistence, and context management
- 📊 **Live Limit Tracking** - Real-time token usage display in status bar
- 🔀 **Multiple contexts** - Work on different branches/tasks in parallel (v0.2+)
- 🔍 **Review-first git workflow** - See diffs, approve changes before commits (v0.3+)
- 💾 **Auto Session Persistence** - Captures session data automatically at thresholds

**Current Status:** 🎯 Planning phase - v0.1 MVP in development (6-month timeline)

---

## Why not just use Claude Desktop?

Claude Desktop is great, but developers need more:

- **Manual tool loading** - Repeatedly calling `tool_search` for the same tools
- **Context switching pain** - Juggling multiple tasks requires multiple windows
- **Blind commits** - Can't easily review what Claude changed before committing
- **Usage anxiety** - No clear visibility into limit consumption
- **Data loss on crashes** - Sessions disappear without session persistence
- **Not truly native** - Electron app with XWayland issues on Wayland


native-claude-client solves these with:

- **Auto tool loading** - Domain-aware tool pre-loading on session start
- **Failure recovery** - Automatic tool loading after consecutive failures
- **Live status bar** - Real-time token usage with color-coded warnings
- **Multi-location persistence** - Sessions saved to 3 locations automatically
- **Native performance** - Pure GTK4/Wayland integration

---

## Hook System Architecture

The hook system is the intelligence layer that makes native-claude-client proactive instead of reactive:

**Phase 2 - Event System (v0.1 MVP):**

- EventBus for pub/sub event routing
- EventEmitter detects conditions (failures, thresholds, session boundaries)
- FailureTracker monitors tool failures per family with velocity detection
- TokenMonitor tracks usage and emits at 60%, 80%, 85%, 90% thresholds
- HookExecutor loads and executes hooks when events fire

**Active Hooks:**

- `predictive-tool-loader` - Pre-loads tools based on domain (Professional, Creative, Balance)
- `auto-tool-loader` - Automatically loads tools after 3 consecutive failures
- `session-end` - Writes session summaries to 3 locations (Notion + Local + Drive)
- `auto-compact` - Proactive context management at 60% threshold (vs panic at 95%)
- `decision-validator` - Enforces "always explain why" protocol
- `focus-shepherd` - Tangent detection and discontinuity mitigation (optional)

**Documentation:**

- [Event System Architecture](docs/event-system.md)
- [Phase 2 Implementation Guide](docs/phase-2-implementation.md)
- [Hook Integration Plan](docs/hooks-integration.md)

**FOUNDATION Integration:**

- Boots from `{INSTANCE_HOME}/.claude/FOUNDATION` directory
- Loads identity files, hooks registry, and user configuration
- Symlinks to Substrate for single source of truth
- Graceful fallback if FOUNDATION missing

###### See [Discussion: FOUNDATION Integration](https://github.com/continuity-bridge/native-claude-client/discussions/3) for community feedback.

native-claude-client solves these developer-specific problems.

---

## Roadmap

**v0.1 MVP (March - August 2026):**

- Single conversation pane
- Claude API integration
- **Event System Foundation** (EventBus, EventEmitter, FailureTracker, TokenMonitor)
- **Hook Executor Engine** with registry/config loading
- **Active Hooks:** predictive-tool-loader, auto-tool-loader, session-end
- **Status bar widget** for live token display
- **FOUNDATION boot detection** and identity loading
- Basic diff viewer (read-only)
- Session persistence (via hooks)

**v0.2 Multi-Session (Sep - Oct 2026):**

- Tabbed/paned interface
- Multiple parallel sessions
- Per-session tracking
- Discord integration (Grand Archivist search widget)

**v0.3 Git Integration (Nov - Dec 2026):**

- Interactive diff staging
- Commit composer
- Branch switcher

**v1.0 Full Release (Jan 2027):**

- GNOME HIG polish
- Plugin architecture
- Complete documentation

See [Roadmap](https://github.com/continuity-bridge/native-claude-client/wiki/Roadmap) for detailed timeline.

---

## Get Involved

We're in the planning phase - perfect time to shape the project!

**Active Discussions:**

[Window Layout: Tabs vs Panes vs Hybrid?](https://github.com/continuity-bridge/native-claude-client/discussions/1)

[What features would make this useful for your workflow?](https://github.com/continuity-bridge/native-claude-client/discussions/2)

[Support loading FOUNDATION utilities and tools](https://github.com/continuity-bridge/native-claude-client/discussions/3)

Ways to contribute:

- Share your workflow pain points in [Discussions](https://github.com/continuity-bridge/native-claude-client/discussions)
- Vote on design decisions
- Review hook system architecture docs
- Test on your distro when v0.1 releases
- Contribute code (after MVP - see [CONTRIBUTING.md](CONTRIBUTING.md))

---

## Installation

**Status:** Not yet released - in development

When v0.1 is ready:

```bash
# Requirements: Python 3.11+, GTK4, Wayland
pip install native-claude-client
native-claude-client
```

For development setup, see [Wiki: Development Setup](https://github.com/continuity-bridge/native-claude-client/wiki/Development-Setup).

---

## Licensing

**Open Source:** GPL-3.0 (see [LICENSE](LICENSE))

**Commercial Licensing:** Available for companies that need GPL exceptions.

**What does this mean?**

- Individual developers and GPL-compatible projects: Free forever
- Companies building proprietary products: Contact for commercial licensing
- All code stays open source regardless

See [Wiki: Design Decisions](https://github.com/continuity-bridge/native-claude-client/wiki/Design-Decisions#license-dual-licensing-gpl-30--commercial) for details on dual licensing.

---

## Project Links

- **Roadmap:** [Wiki: Roadmap](https://github.com/continuity-bridge/native-claude-client/wiki/Roadmap)
- **Design Decisions:** [Wiki: Design Decisions](https://github.com/continuity-bridge/native-claude-client/wiki/Design-Decisions)
- **Discussions:** [Community Forum](https://github.com/continuity-bridge/native-claude-client/discussions)
- **Project Board:** [Development Progress](https://github.com/orgs/continuity-bridge/projects/2)
- **Hook System Docs:** [docs/](docs/)

---

## Part of continuity-bridge

This project is part of the [continuity-bridge](https://github.com/continuity-bridge) ecosystem - infrastructure for AI instance persistence and continuity.

**Related Projects:**

- [unified-limit-monitor](https://github.com/continuity-bridge/unified-limit-monitor) - Track Claude usage limits
- [temporal-awareness-protocol](https://github.com/continuity-bridge/temporal-awareness-protocol) - Time reference for instances
- [continuity-bridge.github.io](https://continuity-bridge.github.io/continuity-bridge/) - Project website

---

**Built by [Jerry Jackson](https://github.com/UncleTallest) (Uncle Tallest)**
