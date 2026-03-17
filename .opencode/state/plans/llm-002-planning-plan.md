# LLM-002 Implementation Plan: OpenCode Adapter and Session-Aware Coding-Agent Routing

## Overview

Ticket LLM-002 adds OpenCode-specific adapter support and session handling for coding-agent workflows. This extends the base `chat_llm` tool from LLM-001 with OpenCode-specific capabilities including conversation history management, working directory context, and coding-agent response formatting.

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|---------------|
| 1 | OpenCode backend routing is explicit | Service type validation, dedicated adapter class |
| 2 | Session handling is planned | Session store with CRUD, conversation history, context window management |
| 3 | Coding-agent responses fit the shared tool contract | MCP-compatible response format with proper metadata |

## Context

- **Existing**: `chat_llm` tool from LLM-001 with basic service routing
- **Existing**: `LLMServiceType.OPENCODE` enum in `src/shared/models.py`
- **Existing**: `_build_opencode_payload()` method in `LLMServiceClient`
- **Existing**: `LLMServicePolicy.get_coding_agent_service()` method
- **Dependency**: LLM-001 (completed)

## Implementation Approach

### 1. OpenCode-Specific Adapter

The adapter will extend basic LLM routing with OpenCode-specific features:

**Adapter Responsibilities**:
- Build proper OpenCode API request format (prompt, system, session_id, working_dir, tools)
- Handle OpenCode-specific response parsing (message, tool_calls, artifacts)
- Support tool execution results and artifact references
- Manage working directory context for code execution
- Transform OpenCode responses to MCP-compatible format

**Design Pattern**: Create `OpenCodeAdapter` class in `src/hub/services/opencode_adapter.py` that:
- Wraps `LLMServiceClient` for HTTP communication
- Adds OpenCode-specific payload building
- Handles OpenCode-specific response parsing
- Integrates with session store for conversation history

### 2. Session Handling Mechanism

**Session Store Design** (`src/hub/services/session_store.py`):
- In-memory session storage (can be swapped for Redis later)
- Session data: conversation history, working directory, metadata
- CRUD operations: create, get, update, delete, list
- Configurable context window (max messages retained)
- Session expiry and cleanup

**Session Data Model**:
```python
class Session:
    session_id: str
    service_id: str
    messages: list[Message]  # conversation history
    working_dir: str | None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
```

### 3. Integration with Existing chat_llm

The implementation extends, not replaces, the existing `chat_llm` tool:

- **New Tool**: `chat_opencode` - specialized OpenCode interaction
- **Session Integration**: New tool uses session store for conversation continuity
- **Shared Components**: Both use `LLMServicePolicy` for service validation
- **Response Contract**: Both return MCP-compatible response format

## New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/services/opencode_adapter.py` | OpenCode-specific HTTP adapter with payload building and response parsing |
| `src/hub/services/session_store.py` | In-memory session store for conversation history and context |
| `src/hub/tools/opencode.py` | OpenCode-specific tool handler with session support |
| `tests/hub/services/test_opencode_adapter.py` | Unit tests for OpenCode adapter |
| `tests/hub/services/test_session_store.py` | Unit tests for session store |

## Existing Files to Modify

| File | Modification |
|------|--------------|
| `src/hub/dependencies.py` | Add DI providers for `OpenCodeAdapter` and `SessionStore` |
| `src/hub/tools/__init__.py` | Register `chat_opencode` tool in `register_llm_tools()` |
| `src/shared/models.py` | Add `Message` and `SessionData` models (optional, can use dict) |

## Detailed Implementation Steps

### Step 1: Create Session Store

**File**: `src/hub/services/session_store.py`

```python
class SessionStore:
    """In-memory store for OpenCode session state."""
    
    def __init__(self, max_history: int = 50):
        self._sessions: dict[str, dict] = {}
        self._max_history = max_history
    
    async def create_session(
        self,
        session_id: str,
        service_id: str,
        working_dir: str | None = None,
    ) -> dict:
        """Create new session with conversation history."""
    
    async def get_session(self, session_id: str) -> dict | None:
        """Get session by ID."""
    
    async def add_message(
        self,
        session_id: str,
        role: str,  # "user" | "assistant" | "system"
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Add message to conversation history."""
    
    async def get_history(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict]:
        """Get conversation history."""
    
    async def update_working_dir(
        self,
        session_id: str,
        working_dir: str,
    ) -> dict | None:
        """Update working directory for session."""
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and cleanup."""
    
    async def list_sessions(self, service_id: str | None = None) -> list[dict]:
        """List all sessions, optionally filtered by service."""
```

### Step 2: Create OpenCode Adapter

**File**: `src/hub/services/opencode_adapter.py`

```python
from typing import Any

class OpenCodeAdapter:
    """OpenCode-specific adapter with session support."""
    
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        session_store: SessionStore,
        default_timeout: float = 180.0,  # Longer for coding tasks
    ):
        self._client = http_client
        self._sessions = session_store
        self._default_timeout = default_timeout
    
    async def chat(
        self,
        service: LLMServiceInfo,
        prompt: str,
        session_id: str | None = None,
        working_dir: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: list[dict] | None = None,
        include_history: bool = True,
    ) -> dict[str, Any]:
        """Send chat request to OpenCode with session support."""
    
    def _build_payload(
        self,
        prompt: str,
        session_id: str | None,
        working_dir: str | None,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
        tools: list[dict] | None,
        history: list[dict] | None,
    ) -> dict:
        """Build OpenCode-specific payload."""
    
    def _parse_response(self, response: dict) -> dict:
        """Parse OpenCode response into MCP-compatible format."""
```

### Step 3: Create OpenCode Tool Handler

**File**: `src/hub/tools/opencode.py`

```python
async def chat_opencode_handler(
    service_id: str | None = None,
    service_name: str | None = None,
    prompt: str = "",
    session_id: str | None = None,
    working_dir: str | None = None,
    system_prompt: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    include_history: bool = True,
    llm_service_policy: "LLMServicePolicy | None" = None,
    opencode_adapter: "OpenCodeAdapter | None" = None,
) -> dict[str, Any]:
    """Handle chat_opencode tool invocation."""
```

### Step 4: Update Dependencies

**File**: `src/hub/dependencies.py`

Add:
- `get_session_store()` - DI provider for session store
- `get_opencode_adapter()` - DI provider for OpenCode adapter
- Update `get_policy_router()` to include new dependencies

### Step 5: Register Tool

**File**: `src/hub/tools/__init__.py`

Update `register_llm_tools()` to include:

```python
def register_llm_tools(registry: ToolRegistry) -> None:
    # ... existing chat_llm registration ...
    
    # Register chat_opencode tool
    registry.register(
        ToolDefinition(
            name="chat_opencode",
            description="Send a coding prompt to OpenCode with session support. "
            "Maintains conversation history across requests when session_id is provided. "
            "Supports working directory context for file operations. "
            "Returns OpenCode response including artifacts and tool executions.",
            handler=chat_opencode_handler,
            parameters={...},
            policy=LLM_REQUIREMENT,
        )
    )
```

## Validation Plan

### Unit Tests

| Component | Test Cases |
|-----------|------------|
| SessionStore | create, get, add_message, get_history, update_working_dir, delete, list |
| OpenCodeAdapter | build_payload, parse_response, chat_with_session, chat_without_session |
| chat_opencode_handler | with_session, without_session, invalid_service, timeout_handling |

### Integration Tests

- Session persistence across multiple requests
- Working directory context propagation
- Service validation before session access
- Response format matches MCP contract

### Validation Commands

```bash
# Run tests
pytest tests/hub/services/test_session_store.py -v
pytest tests/hub/services/test_opencode_adapter.py -v

# Lint
ruff check src/hub/services/session_store.py src/hub/services/opencode_adapter.py src/hub/tools/opencode.py
```

## Integration Points

| Component | Integration |
|-----------|-------------|
| LLMServicePolicy | Used for service validation before adapter use |
| LLMServiceClient | Base HTTP communication (adapter wraps this pattern) |
| ToolRegistry | New tool registration with policy requirement |
| Dependencies | DI providers for new components |

## Risks and Assumptions

| Risk | Mitigation |
|------|------------|
| Session store in-memory only | Design allows swapping to Redis later; document limitation |
| OpenCode API format changes | Version check in adapter, fail gracefully |
| Session expiry not implemented | Add TTL in future; document in code |

## Blockers

None. All required components exist:
- LLM service registry from CORE-002 ✓
- Base chat_llm from LLM-001 ✓
- LLMServiceType.OPENCODE enum ✓
- LLMServicePolicy.get_coding_agent_service() ✓
