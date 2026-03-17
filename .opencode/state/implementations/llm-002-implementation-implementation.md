# LLM-002 Implementation Summary: OpenCode Adapter and Session-Aware Coding-Agent Routing

## Overview

Ticket LLM-002 adds OpenCode-specific adapter support and session handling for coding-agent workflows. This extends the base `chat_llm` tool from LLM-001 with OpenCode-specific capabilities including conversation history management, working directory context, and coding-agent response formatting.

## Changes Made

### New Files Created

1. **`src/hub/services/session_store.py`** - Session management store
   - `SessionStore` class with in-memory session storage
   - CRUD operations: create_session, get_session, add_message, get_history, update_working_dir, delete_session, list_sessions
   - Configurable max history (default 50 messages)
   - Session expiry/cleanup functionality
   - Thread-safe dictionary-based storage

2. **`src/hub/services/opencode_adapter.py`** - OpenCode-specific HTTP adapter
   - `OpenCodeAdapter` class wrapping HTTP client with session support
   - `chat()` method with full session management integration
   - OpenCode-specific payload building with history, working_dir, tools support
   - Response parsing supporting multiple formats (direct, OpenAI-compatible, choices array)
   - Timeout handling (default 180s for coding tasks)
   - Automatic conversation history storage in sessions

3. **`src/hub/tools/opencode.py`** - chat_opencode tool handler
   - `chat_opencode_handler` - Main tool entry point
   - `chat_opencode_impl` - Internal implementation with service validation
   - Full integration with LLMServicePolicy for service validation
   - Session support with working directory context

### Modified Files

1. **`src/hub/dependencies.py`** - Added DI providers
   - Added imports for SessionStore and OpenCodeAdapter
   - Added `get_session_store()` - Global session store singleton
   - Added `get_opencode_adapter()` - Request-scoped OpenCode adapter
   - Updated `get_policy_aware_router()` to inject OpenCodeAdapter

2. **`src/hub/tools/__init__.py`** - Registered chat_opencode tool
   - Added `chat_opencode` tool registration in `register_llm_tools()`
   - Tool parameters: service_id, service_name, prompt, session_id, working_dir, system_prompt, max_tokens, temperature, include_history
   - Policy: LLM_REQUIREMENT

3. **`src/hub/tool_routing/policy_router.py`** - Added dependency injection
   - Added OpenCodeAdapter to TYPE_CHECKING imports
   - Added opencode_adapter parameter to PolicyAwareToolRouter.__init__
   - Updated _execute_handler to inject opencode_adapter when handler accepts it

## Acceptance Criteria Verification

| Criterion | Status | Notes |
|-----------|--------|-------|
| OpenCode backend routing is explicit | ✓ | Service type validation via LLMServicePolicy, dedicated OpenCodeAdapter class |
| Session handling is planned | ✓ | SessionStore with CRUD, conversation history (50 messages), working_dir context |
| Coding-agent responses fit the shared tool contract | ✓ | MCP-compatible response format with success, response, latency_ms, model, tokens_used, artifacts, tool_calls |

## Integration Points

| Component | Integration |
|-----------|-------------|
| LLMServicePolicy | Used for service validation before adapter use |
| LLMServiceClient | Base HTTP communication pattern (adapter wraps similar approach) |
| ToolRegistry | New chat_opencode tool registered with LLM_REQUIREMENT policy |
| Dependencies | DI providers for SessionStore and OpenCodeAdapter |
| PolicyAwareToolRouter | Updated to inject OpenCodeAdapter into handlers |

## Validation

All ruff checks pass:
```bash
ruff check src/hub/services/session_store.py src/hub/services/opencode_adapter.py src/hub/tools/opencode.py src/hub/dependencies.py src/hub/tools/__init__.py src/hub/tool_routing/policy_router.py
```

## Notes

- Session store is in-memory only (can be swapped to Redis later)
- OpenCode adapter uses 180s default timeout (longer for coding tasks)
- Working directory context is maintained per session
- Conversation history is automatically stored and included in subsequent requests
- Response parsing handles multiple common OpenCode API response formats
