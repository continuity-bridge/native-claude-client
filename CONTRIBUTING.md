# Contributing to claude-devel-client

Thanks for your interest in contributing! This project is in early planning stages (pre-v0.1), so the best ways to help are evolving.

---

## Current Phase: Planning → v0.1 MVP

**Timeline:** March - August 2026 (6 months)  
**Status:** Design decisions in progress, no code yet

**Best ways to contribute right now:**
1. **Share your workflow** in [Discussions](https://github.com/continuity-bridge/claude-devel-client/discussions)
2. **Vote on design decisions** (window layout, git integration depth, etc.)
3. **Report bugs** when v0.1 releases (testing will be critical)

**Not ready yet:**
- Code contributions (no codebase exists)
- Documentation writing (architecture still forming)
- Plugin development (v1.0 feature)

---

## How to Get Involved

### 1. Join Discussions

The best way to shape the project is through [Discussions](https://github.com/continuity-bridge/claude-devel-client/discussions).

**Active topics:**
- [Window Layout: Tabs vs Panes vs Hybrid?](https://github.com/continuity-bridge/claude-devel-client/discussions/1)
- [What features would make this useful for your workflow?](https://github.com/continuity-bridge/claude-devel-client/discussions/2)

**Discussion categories:**
- **💡 Ideas** - Feature proposals and suggestions
- **🎨 Design Decisions** - UI/UX and architecture discussions
- **❓ Q&A** - Questions about the project
- **🐛 Bug Reports** - Discuss bugs before creating issues (post-v0.1)
- **🔧 Development** - Contributor discussions (post-v0.1)

### 2. Provide Feedback

We especially want to hear from:
- Developers who use Claude for coding daily
- Linux desktop enthusiasts who care about native apps
- Git power users who have opinions on review workflows
- People frustrated with Claude Desktop's limitations

**Be specific!** "Better git integration" is less helpful than "I want to review diffs file-by-file, not see all changes at once."

### 3. Test on Your Distro

When v0.1 releases (target: August 2026), testing on different distros will be critical.

**We'll need testers on:**
- Ubuntu / Debian
- Fedora / RHEL
- Arch / Manjaro
- openSUSE
- Other GTK-based desktops

---

## Code Contributions (Post-v0.1)

Once the codebase exists, here's how to contribute code:

### Before You Start

**For bug fixes:**
- Just submit a PR with the fix
- Include steps to reproduce the bug

**For new features:**
- Open an issue first to discuss
- Avoids wasted work if feature doesn't fit roadmap
- Lets us refine the approach together
- Ensures you're not duplicating ongoing work

**For major architectural changes:**
- Open a Discussion in the Design Decisions category
- These affect everything, need broader input

### Development Setup

See [Wiki: Development Setup](https://github.com/continuity-bridge/claude-devel-client/wiki/Development-Setup) for environment configuration (coming soon).

**Requirements:**
- Python 3.11+
- GTK4 / PyGObject
- Linux (Wayland preferred)

### Code Style

We follow:
- [PEP 8](https://pep8.org/) for Python
- [GNOME HIG](https://developer.gnome.org/hig/) for UI/UX
- Docstrings for all public functions
- Type hints where helpful

Detailed style guide coming after v0.1.

### Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test locally (manual testing for now, automated tests later)
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

**PR guidelines:**
- Clear title describing the change
- Description explaining *why* (not just *what*)
- Link to related issue/discussion if applicable
- One logical change per PR (not 5 unrelated fixes)

**Review process:**
- Maintainer will review within a few days
- May request changes or clarification
- PRs that don't fit project goals will be closed with explanation
- All PRs require maintainer approval to merge

---

## What We're Looking For

**Contributions that align with project principles:**
1. **Native first** - Truly native Linux, not web wrappers
2. **Developer-focused** - Solve developer pain points
3. **Review-first** - Transparency before action
4. **Maintainable** - Simple over clever

**Contributions we'll likely decline:**
- Features that only work on Windows/Mac
- Dependencies on Electron or web technologies
- Telemetry or tracking of any kind
- Complexity without clear user benefit
- Features that conflict with roadmap priorities

This isn't personal - it's about keeping the project focused.

---

## Licensing

By contributing, you agree that your contributions will be licensed under GPL-3.0.

If you need a commercial exception for your employer's use, contact the maintainer to discuss dual licensing terms.

---

## Code of Conduct

**Be respectful, be constructive, be honest.**

- Assume good faith
- Critique ideas, not people
- Welcome newcomers
- No harassment, discrimination, or trolling
- Maintainer decisions are final

Violations will result in removal from the project.

---

## Questions?

- **General questions:** [Q&A Discussions](https://github.com/continuity-bridge/claude-devel-client/discussions/categories/q-a)
- **Design questions:** [Design Decisions](https://github.com/continuity-bridge/claude-devel-client/discussions/categories/design-decisions)
- **Bugs (post-v0.1):** [Issues](https://github.com/continuity-bridge/claude-devel-client/issues)

---

## Thank You

Building native Linux tools for developers takes time and effort. Your contributions - whether code, feedback, or testing - help make this real.

**Current maintainer:** Jerry Jackson ([@UncleTallest](https://github.com/UncleTallest))

Let's build something great together.
