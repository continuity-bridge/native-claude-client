# Hook Integration Plan for v0.1 MVP

**Version:** 1.0.0  
**Target:** Erebos v0.1 MVP (March - August 2026)  
**Author:** Vector/Shepard + Uncle Tallest  
**Created:** 2026-04-01

---

## Executive Summary

The hook system transforms Erebos from a "smart chat app" into an **agentic development environment**. This document shows how hooks integrate with v0.1 MVP features to deliver:

✅ **Zero-friction tool loading** - Never type `tool_search` again  
✅ **Automatic session persistence** - Work is always captured  
✅ **Smart context management** - Rotate before degradation, not after  
✅ **Self-improving profiles** - Learns your actual workflow

**Strategic Value:** Hooks solve the #1 developer pain point with Claude Desktop - **manual tool loading** - while establishing infrastructure for all future automation.

---

## v0.1 MVP Features (from README)

| Feature                       | Status | Hook Integration             |
| ----------------------------- | ------ | ---------------------------- |
| Single conversation pane      | Core   | ✅ Session start/end hooks   |
| Claude API integration        | Core   | ✅ Tool failure detection    |
| Basic diff viewer (read-only) | Core   | ⏳ Future: git hooks         |
| Limit tracking display        | Core   | ✅ Token threshold hooks     |
| Session persistence           | Core   | ✅ **PRIMARY HOOK USE CASE** |

---

## Hook System Value Proposition

### For MVP Users (March - August 2026)

**Without Hooks:**

1. Start conversation
2. Try to use Filesystem tool → Error: "Tool not loaded"
3. Manually call `tool_search(query="filesystem")`
4. Wait 3-5 seconds
5. Try tool again → Success
6. Repeat for Calendar, Notion, etc.
7. Conversation ends → No automatic summary
8. Session data lost if app crashes

**With Hooks:**

1. Start conversation → **Hooks auto-load tools based on domain**
2. Tools just work immediately
3. If tool fails 3 times → **Hook auto-loads it**
4. At 60% tokens → **Hook offers to rotate context**
5. Conversation ends → **Hook writes session summary to 3 locations**

**User Experience:** Tools are transparent, sessions are persistent, workflow is uninterrupted.

---

## Integration Architecture

### System Components

```
┌─────────────────────────────────────────────────┐
│         Erebos v0.1               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐      ┌──────────────┐        │
│  │ GTK4 UI      │◄────►│ Claude API   │        │
│  │ (Chat Pane)  │      │ Client       │        │
│  └──────┬───────┘      └──────┬───────┘        │
│         │                     │                 │
│         │   ┌─────────────────▼──────────┐     │
│         └──►│   Event System (Phase 2)   │     │
│             │   - EventBus               │     │
│             │   - EventEmitter           │     │
│             │   - FailureTracker         │     │
│             │   - TokenMonitor           │     │
│             └──────────┬─────────────────┘     │
│                        │                       │
│             ┌──────────▼─────────────┐         │
│             │  Hook Executor Engine  │         │
│             │  - Loads registry      │         │
│             │  - Executes hooks      │         │
│             └──────────┬─────────────┘         │
│                        │                       │
│             ┌──────────▼─────────────┐         │
│             │  Substrate Hooks       │         │
│             │  (symlinked from       │         │
│             │   ~/Substrate/.claude) │         │
│             └────────────────────────┘         │
└─────────────────────────────────────────────────┘
```

---

## Hook-Feature Integration Matrix

### Feature 1: Session Persistence

**MVP Requirement:** "Pick up where you left off"

**Hook Integration:**

**session-end hook:**

- **Trigger:** User closes app, types "wrap up", or 85% token budget
- **Action:** Write session summary to:
  1. Notion Session Log database (PRIMARY)
  2. Local `~/Substrate/Docs/SESSION-SUMMARY-*.md`
  3. Google Drive `Cognate-Quarters/session-logs/`
- **Data Captured:**
  - Conversation duration
  - Files created/modified
  - Decisions made
  - Tools used
  - Next steps for resume

**Implementation:**

```python
# In ClaudeClient.close_conversation()
def close_conversation(self):
    # Existing MVP code
    self.save_chat_history()

    # NEW: Emit session_end event
    self.emitter.end_session(trigger="user_action")

    # Hook automatically writes to 3 locations
    # No manual persistence code needed!
```

**User Experience:**

- Close app mid-conversation
- Reopen next day
- Check Notion Session Log → See complete summary
- Understand context instantly
- Resume work seamlessly

---

### Feature 2: Claude API Integration

**MVP Requirement:** "Send/receive messages, handle API errors"

**Hook Integration:**

**predictive-tool-loader hook:**

- **Trigger:** `session_start` event
- **Action:** Pre-load tools based on detected domain
  - Professional → Filesystem, Calendar, Gmail, Atlassian
  - Creative → Filesystem, Notion
  - Default → Filesystem only

**auto-tool-loader hook:**

- **Trigger:** 3 consecutive tool failures (velocity-aware)
- **Action:** Automatically call `tool_search` for failed family
- **Recovery:** Tools available for retry

**Implementation:**

```python
# In ClaudeClient.call_tool()
def call_tool(self, tool_name: str, params: dict):
    try:
        result = self.api.call_tool(tool_name, params)
        return result
    except ToolNotLoadedError as e:
        # NEW: Emit failure event
        family = self._detect_family(tool_name)
        self.emitter.tool_failed(tool_name, family, "not_loaded", str(e))

        # FailureTracker counts this
        # After 3 failures, auto-tool-loader hook fires
        # Hook calls tool_search automatically

        raise  # Let UI handle user-facing error
```

**User Experience:**

- Try to use Calendar tool → Fails (not loaded)
- Try again → Fails
- Try third time → **Hook auto-loads Calendar tools**
- Next attempt → Success
- No manual intervention required

---

### Feature 3: Limit Tracking Display

**MVP Requirement:** "Know your usage across all sessions"

**Hook Integration:**

**auto-compact hook:**

- **Trigger:** 60% token budget (proactive)
- **Action:**
  1. Capture pre-compact state
  2. Recommend compact message to user
  3. After compact, suggest scaffolding reload

**Implementation:**

```python
# In ClaudeClient.send_message()
def send_message(self, message: str):
    response = self.api.messages.create(...)

    # NEW: Update token monitor
    total_tokens = response.usage.input_tokens + response.usage.output_tokens
    self.token_monitor.update(total_tokens)

    # TokenMonitor emits events at 60%, 80%, 85%, 90%
    # auto-compact hook listens for 60%
    # Shows UI notification: "Consider rotating context"

    # Update UI progress bar
    self.ui.update_token_display(total_tokens, self.max_tokens)

    return response
```

**User Experience:**

- UI shows token progress bar
- At 60% → Notification: "Good time to rotate context (git commit just completed)"
- Click → Suggested compact message pre-filled
- Rotate cleanly before degradation
- No panic mode at 95%

---

## Domain Detection Strategy

**Critical:** Hooks need to know which domain user is in to load correct tools.

### Detection Methods

**Method 1: Project Directory (v0.1)**

```python
def detect_domain_from_path(cwd: str) -> str:
    """Detect domain from current working directory."""
    if "Devel" in cwd or "code" in cwd:
        return "domain_1_professional"
    elif "creative" in cwd or "writing" in cwd:
        return "domain_2_creative"
    elif "balance" in cwd:
        return "domain_3_balance"
    else:
        return "default"
```

**Method 2: Domain Primer File (v0.2+)**

```python
# Check for .claude-domain file in project root
def detect_domain_from_primer() -> str:
    """Read domain from .claude-domain file."""
    primer_path = Path(".claude-domain")
    if primer_path.exists():
        return primer_path.read_text().strip()
    return "default"
```

**Method 3: User Selection (v0.1 fallback)**

```python
# UI dropdown on session start
# "Which workspace are you in?"
# - Professional (Development)
# - Creative (Writing/Design)
# - Balance (Personal)
# - Let me choose tools manually
```

---

## File Organization

### Symlinks to Substrate

**Why:** Hooks are defined in Substrate (ground truth), but Erebos needs access.

**Setup:**

```bash
# In Erebos repo
ln -s ~/Substrate/.claude/FOUNDATION/hooks/hooks-registry.json \
  erebos/config/hooks-registry.json

ln -s ~/Substrate/.claude/FOUNDATION/hooks/hooks-config.json \
  erebos/config/hooks-config.json

ln -s ~/Substrate/.claude/FOUNDATION/hooks/executors \
  erebos/hooks/executors
```

**Benefit:**

- Single source of truth in Substrate
- Changes sync automatically
- Erebos stays lean
- Works across Claude Desktop, Web, Mobile

---

## Hook Execution Flow (v0.1)

### Scenario: Professional Developer Starting Session

**Step 1: App Launch**

```
User opens Erebos
  ↓
SessionManager.start_session()
  ↓
Domain detection → "domain_1_professional"
  ↓
EventEmitter.start_session(domain="domain_1_professional")
  ↓
EventBus emits session_start event
  ↓
HookExecutor receives event
  ↓
Checks hooks-registry.json → predictive-tool-loader enabled
  ↓
Loads hook config → domain_1_professional tools = [Filesystem, Calendar, Gmail]
  ↓
Hook executes: tool_search(query="filesystem calendar gmail", limit=10)
  ↓
Tools loaded in background (2-5 seconds)
  ↓
User can use tools immediately (or after brief load)
```

**User sees:**

- App opens
- Brief "Loading workspace tools..." spinner (2-3s)
- Tools ready to use
- No manual tool_search needed

---

### Scenario: Tool Failure Recovery

**Step 1: User tries Notion (not pre-loaded)**

```
User: "Create a page in Notion"
  ↓
ClaudeClient.call_tool("Notion:create-page", {...})
  ↓
API Error: Tool not loaded
  ↓
EventEmitter.tool_failed("Notion:create-page", "Notion", "not_loaded")
  ↓
FailureTracker increments: Notion failures = 1
  ↓
(Threshold is 3, no action yet)
```

**Step 2: Second attempt**

```
User tries again (or different Notion tool)
  ↓
Another failure
  ↓
FailureTracker: Notion failures = 2
  ↓
(Still below threshold)
```

**Step 3: Third attempt**

```
Third failure
  ↓
FailureTracker: Notion failures = 3
  ↓
Threshold reached! Emit failure_threshold event
  ↓
HookExecutor receives event
  ↓
auto-tool-loader hook executes
  ↓
Hook: tool_search(query="notion", limit=10)
  ↓
Notion tools now loaded
  ↓
User's next attempt succeeds
```

**User sees:**

- First 3 attempts fail with "Tool not loaded"
- Brief "Loading Notion tools..." notification
- Fourth attempt succeeds
- No manual intervention

---

## Phased Rollout Strategy

### Phase 1: MVP Foundation (v0.1)

**Hooks to Enable:**

1. ✅ predictive-tool-loader
2. ✅ auto-tool-loader
3. ✅ session-end

**Why These:**

- Solve immediate pain (tool loading)
- Deliver session persistence (MVP requirement)
- Low implementation complexity
- High user value

**Not Yet:**

- ❌ auto-compact (requires more UI work)
- ❌ tool-usage-analyzer (needs data first)
- ❌ decision-validator (future enhancement)
- ❌ focus-shepherd (too intrusive for MVP)

---

### Phase 2: Analytics & Optimization (v0.2)

**Add:**

- tool-usage-analyzer (weekly reports)
- auto-compact (with UI prompts)

**Goal:** Self-improving system that adapts to user

---

### Phase 3: Advanced Automation (v0.3+)

**Add:**

- decision-validator (for git workflows)
- focus-shepherd (tangent detection)
- Custom hooks (user-defined)

---

## User-Facing Changes

### Settings Panel

**New Section: "Workspace Automation"**

```
┌─────────────────────────────────────┐
│ Workspace Automation                │
├─────────────────────────────────────┤
│                                     │
│ ☑ Auto-load tools on session start  │
│   Pre-loads tools based on domain   │
│                                     │
│ ☑ Auto-recover from tool failures   │
│   Loads tools after 3 failed calls  │
│                                     │
│ ☑ Capture session summaries         │
│   Writes to Notion + local on end   │
│                                     │
│ ☐ Proactive context rotation        │
│   Suggests compact at 60% tokens    │
│   (Coming in v0.2)                  │
│                                     │
│ Current Domain: Professional ▼      │
│                                     │
│ [Advanced Hook Settings...]         │
│                                     │
└─────────────────────────────────────┘
```

---

### Status Indicators

**Bottom status bar:**

```
Session: 1.2 hours │ Tokens: 45,231/200,000 (23%) │ Tools: 8 loaded │ Domain: Professional
```

**Hover tooltips:**

- "8 tools loaded" → Shows which families (Filesystem, Calendar, etc.)
- "Domain: Professional" → Explains what this means

---

## Success Metrics

### v0.1 MVP Goals

**Quantitative:**

- ✅ Zero manual `tool_search` calls (100% reduction)
- ✅ 100% session capture rate (vs 0% without hooks)
- ✅ <3s tool loading time on session start
- ✅ 95%+ tool call success rate after auto-load

**Qualitative:**

- ✅ "Tools just work" (user interviews)
- ✅ "I trust my work is saved" (confidence)
- ✅ "Faster than Claude Desktop" (benchmark)

### Data to Track

**Week 1-4:**

- Tool load events per session
- Auto-load trigger count
- Session summary write success rate
- User-reported friction points

**Month 2+:**

- Domain profile accuracy
- Tools pre-loaded but never used (waste)
- Tools auto-loaded (should've been pre-loaded)
- Time saved vs manual tool loading

---

## Risk Mitigation

### Risk 1: Wrong Domain Detection

**Impact:** Loads wrong tools, user has to wait for auto-load

**Mitigation:**

- Provide manual domain selector in UI
- Remember user's choice per project directory
- Allow override via `.claude-domain` file
- Default to safe "Filesystem only" if uncertain

---

### Risk 2: Hook Execution Failures

**Impact:** Tools don't load, sessions don't save

**Mitigation:**

- Comprehensive error logging
- Fallback to manual tool_search if hook fails
- UI notification: "Automation failed, please load tools manually"
- Hooks are additive (app works without them)

---

### Risk 3: Performance Overhead

**Impact:** App feels sluggish due to hook processing

**Mitigation:**

- Event bus is in-memory (no I/O)
- Hooks execute async where possible
- Profile with 1000+ events/sec benchmark
- Disable hooks if latency >100ms

---

## Testing Plan

### Unit Tests

- EventBus pub/sub
- EventEmitter event construction
- FailureTracker threshold detection
- TokenMonitor percentage calculation
- HookExecutor registry loading

### Integration Tests

- Full session lifecycle with hooks
- Tool failure → auto-load → success
- Token threshold → UI notification
- Session end → 3-location write

### User Acceptance Tests

- "Start app, use tools, close app" → Session saved?
- "Use unfamiliar tool" → Auto-loads after 3 tries?
- "Work for 2 hours" → Proactive compact offer at 60%?

---

## Documentation Requirements

### For Users

**Quick Start Guide:**

- "Your first session with auto-loaded tools"
- "Understanding workspace domains"
- "Where your session summaries are saved"

**FAQ:**

- "Why did my tools load automatically?"
- "How do I change my workspace domain?"
- "Can I disable automation?"

### For Developers

**Hook Development Guide:**

- How to add custom hooks
- Hook executor markdown format
- Testing hook executors
- Debugging hook failures

---

## Deployment Checklist

**Before v0.1 Release:**

- [ ] Event system implemented (Phase 2)
- [ ] Hooks registry symlinked from Substrate
- [ ] Domain detection working
- [ ] UI settings panel added
- [ ] All hooks tested with real use
- [ ] Error logging comprehensive
- [ ] User documentation complete
- [ ] Performance benchmarked
- [ ] Fallback paths tested (hooks disabled)

---

## Conclusion

Hooks are **not optional** for v0.1 MVP. They're the **differentiator** that makes Erebos superior to Claude Desktop:

**Without hooks:**

- Manual tool loading (friction)
- No session persistence (data loss)
- Panic mode compaction (degraded UX)

**With hooks:**

- Transparent tool management (magic)
- Automatic session capture (trust)
- Proactive context rotation (smooth)

The hook system architecture from March 23-24 is production-ready. The integration path is clear. The user value is massive.

**Recommendation:** Implement Phase 2 (Event System) in Weeks 1-4 of v0.1 development. Everything else builds on this foundation.

---

**Version:** 1.0.0  
**Created:** 2026-04-01  
**Next Review:** After v0.1 MVP release

---

_Automation transforms tools into an environment._
