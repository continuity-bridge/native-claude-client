# native-claude-client
**Native GTK4 client for Claude with agentic development workflows**

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![GTK](https://img.shields.io/badge/GTK-4.0-orange.svg)](https://gtk.org)

---

## What is this?

A native Linux desktop application for Claude that goes beyond chat - it's an **agentic development environment**:

- 🖥️ **Native GTK4/Wayland** - Truly native Linux UI, not Electron
- 🔀 **Multiple contexts** - Work on different branches/tasks in parallel (v0.2+)
- 🔍 **Review-first git workflow** - See diffs, approve changes before commits (v0.3+)
- 📊 **Unified limit tracking** - Know your usage across all sessions
- 💾 **Session persistence** - Pick up where you left off

**Current Status:** 🎯 Planning phase - v0.1 MVP in development (6-month timeline)

---

## Why not just use Claude Desktop?

Claude Desktop is great, but developers need more:

- **Context switching pain** - Juggling multiple tasks requires multiple windows
- **Blind commits** - Can't easily review what Claude changed before committing
- **Usage anxiety** - No clear visibility into limit consumption
- **Not truly native** - Electron app with XWayland issues on Wayland

native-claude-client solves these developer-specific problems.

---

## Roadmap

**v0.1 MVP (March - August 2026):**
- Single conversation pane
- Claude API integration
- Basic diff viewer (read-only)
- Limit tracking display
- Session persistence

**v0.2 Multi-Session (Sep - Oct 2026):**
- Tabbed/paned interface
- Multiple parallel sessions
- Per-session tracking

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
- [Window Layout: Tabs vs Panes vs Hybrid?](https://github.com/continuity-bridge/native-claude-client/discussions/1)
- [What features would make this useful for your workflow?](https://github.com/continuity-bridge/native-claude-client/discussions/2)

**Ways to contribute:**
- Share your workflow pain points in [Discussions](https://github.com/continuity-bridge/native-claude-client/discussions)
- Vote on design decisions
- Test on your distro when v0.1 releases
- Contribute code (after MVP - see [CONTRIBUTING.md](CONTRIBUTING.md))

---

## Installation

**Status:** Not yet released - in development

When v0.1 is ready:
```bash
# Requirements: Python 3.11+, GTK4, Wayland
pip install native-claude-clientnative-claude-client
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

---

## Part of continuity-bridge

This project is part of the [continuity-bridge](https://github.com/continuity-bridge) ecosystem - infrastructure for AI instance persistence and continuity.

**Related Projects:**
- [unified-limit-monitor](https://github.com/continuity-bridge/unified-limit-monitor) - Track Claude usage limits
- [temporal-awareness-protocol](https://github.com/continuity-bridge/temporal-awareness-protocol) - Time reference for instances
- [continuity-bridge.github.io](https://continuity-bridge.github.io/continuity-bridge/) - Project website

---

**Built by [Jerry Jackson](https://github.com/UncleTallest) (Uncle Tallest)**
