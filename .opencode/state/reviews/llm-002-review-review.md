# Code Review: LLM-002 — OpenCode Adapter and Session-Aware Coding-Agent Routing

## Ticket Details

| Field | Value |
|-------|-------|
| ID | LLM-002 |
| Title | OpenCode adapter and session-aware coding-agent routing |
| Stage | review |
| Status | in_progress |

## Review Summary

**Decision: APPROVED**

All three acceptance criteria are satisfied. The implementation is complete, well-structured, and follows the project conventions.

## Acceptance Criteria Verification

| # | Criterion | Status | Verification |
|---|-----------|--------|--------------|
| 1 | OpenCode backend routing is explicit | ✅ PASS | `OpenCodeAdapter` class wraps HTTP client with explicit service validation via `LLMServicePolicy`. Service is validated before any adapter call. |
| 2 | Session handling is planned | ✅ PASS | `SessionStore` class provides full CRUD: create_session, get_session, add_message, get_history, update_working_dir, delete_session, list_sessions. Configurable max history (50), session expiry cleanup implemented. |
| 3 | Coding-agent responses fit the shared tool contract | ✅ PASS | Response format: {success, response, latency_ms, model, tokens_used, artifacts, tool_calls}. MCP-compatible with structured error handling. |

## Implementation Review

### Files Created (3 new)

1. **`src/hub/services/session_store.py`** (245 lines)
   - Complete in-memory session store
   - Async methods for all CRUD operations
   - Session expiry/cleanup with configurable TTL
   - Working directory context per session
   - Proper serialization for responses

2. **`src/hub/services/opencode_adapter.py`** (309 lines)
   - OpenCode-specific HTTP adapter
   - 180s default timeout (longer for coding tasks)
   - Session integration for conversation history
   - Multi-format response parsing (direct, OpenAI-compatible, choices array)
   - Automatic message storage in sessions

3. **`src/hub/tools/opencode.py`** (186 lines)
   - `chat_opencode_handler` main entry point
   - `chat_opencode_impl` internal implementation
   - Service validation before adapter use
   - Full parameter validation

### Files Modified (3)

1. **`src/hub/dependencies.py`** - Added DI providers
   - `get_session_store()` - Global singleton
   - `get_opencode_adapter()` - Request-scoped adapter
   - Updated `get_policy_aware_router()` to inject adapter

2. **`src/hub/tools/__init__.py`** - Registered `chat_opencode` tool
   - Tool parameters: service_id, service_name, prompt, session_id, working_dir, system_prompt, max_tokens, temperature, include_history
   - Policy: LLM_REQUIREMENT

3. **`src/hub/tool_routing/policy_router.py`** - Added DI injection
   - `opencode_adapter` parameter in constructor
   - Handler injection via signature inspection

### Code Quality

- ✅ Complete type hints on all functions
- ✅ Docstrings on all public methods
- ✅ Structured logging with trace_id propagation
- ✅ Proper error handling with structured responses
- ✅ Async/await throughout
- ✅ Follows project conventions from AGENTS.md

### Integration Verification

| Component | Integration | Status |
|-----------|-------------|--------|
| LLMServicePolicy | Service validation before adapter use | ✅ |
| SessionStore | Conversation history management | ✅ |
| ToolRegistry | chat_opencode registered with LLM_REQUIREMENT | ✅ |
| Dependencies | DI providers for SessionStore and OpenCodeAdapter | ✅ |
| PolicyAwareToolRouter | opencode_adapter injected into handlers | ✅ |

## Observations

### Low Severity

1. **In-memory session store limitation**: The SessionStore is in-memory only. The implementation correctly documents this and the design allows swapping to Redis later. Production deployments should consider distributed session storage.

2. **Default parameter pattern**: In `dependencies.py`, the pattern `session_store: SessionStore = None` followed by `if session_store is None` is unconventional but works correctly in Python.

### Not Blockers

- All acceptance criteria satisfied
- Integration points verified
- Code quality meets project standards
- No regressions detected

## Validation Commands

```bash
# Lint check
ruff check src/hub/services/session_store.py src/hub/services/opencode_adapter.py src/hub/tools/opencode.py src/hub/dependencies.py src/hub/tools/__init__.py src/hub/tool_routing/policy_router.py
```

## Recommendation

**APPROVED** — The implementation satisfies all three acceptance criteria. The code is production-ready with proper error handling, logging, and DI integration. The team leader can advance this ticket to QA.
