# Research

This directory contains exploratory work and findings from the planning phase.

## Auth Token Research

**Goal:** Locate and document Claude Desktop authentication tokens

**Status:** Not started

**Key questions:**
- Where does Claude Desktop store auth tokens on Linux?
- What format are they? (JWT, session cookie, API key?)
- How long do they last? Do they refresh?
- Can we use Desktop tokens with the Messages API?

Findings will be documented here before implementation begins.

---

## API Integration Research

**Goal:** Test Anthropic API integration

**Status:** Not started

**Key questions:**
- Does authentication with Desktop tokens work?
- What endpoints are available?
- Rate limits and quota handling
- Error responses and edge cases

---

## GTK4 Prototypes

**Goal:** Experiment with UI patterns

**Status:** Not started

Prototypes for:
- Basic conversation UI
- Markdown rendering
- Diff viewer component
- Session management

---

**Research findings feed directly into architecture decisions.**
