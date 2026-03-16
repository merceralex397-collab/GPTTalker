# Implementation Plan: CORE-003 - Node Agent Service Skeleton

## Overview

Ticket CORE-003 creates the foundational node-agent service shell with config loading, health endpoint, and bounded executor structure. This is the skeleton that will later be connected to the hub over Tailscale (CORE-004) and exposed to MCP tools (REPO-002, REPO-003, WRITE-001).

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Node-agent package shape is defined | FastAPI app exists with proper lifecycle |
| 2 | Health endpoint contract is explicit | `/health` returns node status in known schema |
| 3 | Executor boundary is separate from hub code | `OperationExecutor` is self-contained in node_agent |

---

## Scope

### What's In Scope

1. **FastAPI app shell** for node agent with lifespan management
2. **Health endpoint** (`GET /health`) returning node status
3. **Dependencies injection** pattern matching hub conventions
4. **Executor integration** with bounded path validation
5. **Logging integration** using shared structured logging
6. **Entry point** via `uvicorn` for production and `python -m` for dev

### What's Out of Scope

- Tailscale connectivity to hub (CORE-004)
- Actual file operation implementations (deferred to REPO-002, REPO-003, WRITE-001)
- Hub-to-node communication protocol (CORE-004)
- Node registration with hub (EDGE-002)

---

## Technical Design

### 1. Package Structure

```
src/node_agent/
├── __init__.py           # Package init, exports
├── main.py               # FastAPI app factory, entry point
├── config.py             # NodeAgentConfig (already exists)
├── executor.py           # OperationExecutor (already exists, needs integration)
├── dependencies.py       # NEW: DI providers for node agent
├── lifespan.py           # NEW: Lifecycle management
├── routes/
│   ├── __init__.py       # NEW
│   ├── health.py         # NEW: Health endpoint
│   └── operations.py     # NEW: Operation handlers (stubs for later)
└── models.py             # NEW: Node-specific Pydantic models
```

### 2. FastAPI App Shell

The node agent will use a minimal FastAPI application similar to the hub:

```python
# src/node_agent/main.py
from fastapi import FastAPI
from src.node_agent.lifespan import lifespan

def create_app() -> FastAPI:
    app = FastAPI(
        title="GPTTalker Node Agent",
        description="Lightweight agent service for local repo operations",
        version="1.0.0",
        lifespan=lifespan,
    )
    # Register routes
    from src.node_agent.routes import health, operations
    app.include_router(health.router, tags=["health"])
    app.include_router(operations.router, tags=["operations"])
    return app

app = create_app()
```

### 3. Health Endpoint Design

The health endpoint provides the hub with node status information:

**Route**: `GET /health`

**Response Schema** (`HealthResponse`):

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class HealthResponse(BaseModel):
    """Health check response for node agent."""
    status: Literal["healthy", "degraded", "unhealthy"]
    node_name: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    capabilities: list[str]  # e.g., ["repo_read", "repo_search", "markdown_write"]
    checks: dict[str, bool]  # individual component checks
```

**Implementation** (`src/node_agent/routes/health.py`):

- Returns `200 OK` when healthy
- Returns `503 Service Unavailable` when unhealthy
- Includes basic system checks (config valid, executor initialized)

### 4. Executor Boundary

The `OperationExecutor` class in `executor.py` is already defined with path validation. For this ticket:

1. **Integration**: Instantiate `OperationExecutor` in app state during lifespan startup
2. **Isolation**: Executor is instantiated per-app, not shared with hub
3. **Validation**: All operation routes will depend on the executor from app state

The executor boundary is architecturally separate because:
- It's in the `node_agent` package, not `shared`
- It operates on local paths only
- Hub never directly calls executor—hub sends commands via HTTP to node agent

### 5. Configuration Loading

The existing `NodeAgentConfig` in `config.py` is complete. For this ticket:

1. **Load config** in lifespan startup
2. **Validate** config produces valid instance
3. **Store** in app state for DI

Environment variables (with prefix `GPTTALKER_NODE_`):
- `GPTTALKER_NODE_NODE_NAME` - Node identifier
- `GPTTALKER_NODE_HUB_URL` - Hub URL
- `GPTTALKER_NODE_API_KEY` - Auth key
- `GPTTALKER_NODE_OPERATION_TIMEOUT` - Timeout seconds
- `GPTTALKER_NODE_MAX_FILE_SIZE` - Max file read size
- `GPTTALKER_NODE_ALLOWED_REPOS` - JSON list of allowed repo paths
- `GPTTALKER_NODE_ALLOWED_WRITE_TARGETS` - JSON list of allowed write paths

### 6. Logging Integration

Use shared structured logging:

```python
from src.shared.logging import setup_logging, get_logger

logger = get_logger(__name__)
```

Log at startup:
- Config loaded successfully
- Executor initialized with allowed paths
- Health endpoint registered
- Server ready to accept connections

### 7. Dependencies Injection

New file `src/node_agent/dependencies.py`:

```python
from fastapi import Depends, FastAPI
from src.node_agent.config import NodeAgentConfig, get_node_agent_config
from src.node_agent.executor import OperationExecutor

def get_config(app: FastAPI) -> NodeAgentConfig:
    """Get node agent config from app state."""
    return app.state.config

def get_executor(app: FastAPI) -> OperationExecutor:
    """Get operation executor from app state."""
    return app.state.executor
```

---

## Implementation Steps

### Step 1: Create Dependencies Module

**File**: `src/node_agent/dependencies.py`

Create DI providers for config and executor injection.

### Step 2: Create Lifespan Management

**File**: `src/node_agent/lifespan.py`

Implement async context manager for startup/shutdown:
1. Initialize logging from config
2. Validate and load config
3. Initialize OperationExecutor with allowed paths
4. Store config and executor in app state
5. Log startup completion
6. On shutdown: log termination

### Step 3: Create Health Route

**File**: `src/node_agent/routes/__init__.py`

Create routes package.

**File**: `src/node_agent/routes/health.py`

Implement `/health` endpoint:
- Return `HealthResponse` with node status
- Check that executor is initialized
- Include capabilities list (will expand with REPO-002, etc.)

### Step 4: Create Operations Route (Stubs)

**File**: `src/node_agent/routes/operations.py`

Create placeholder routes that return `501 Not Implemented`:
- `POST /operations/list-dir`
- `POST /operations/read-file`
- `POST /operations/search`
- `POST /operations/git-status`
- `POST /operations/write-file`

These will be implemented in later tickets (REPO-002, REPO-003, WRITE-001).

### Step 5: Create Node Models

**File**: `src/node_agent/models.py`

Define Pydantic models:
- `HealthResponse` - health endpoint response
- `OperationRequest` - base class for operation requests
- `ListDirRequest`, `ReadFileRequest`, etc. - specific requests
- `OperationResponse` - base response with success/error

### Step 6: Update Main Entry Point

**File**: `src/node_agent/main.py`

Refactor to use the new app factory pattern:
- Import and use `create_app()` 
- Add proper `if __name__ == "__main__"` block with uvicorn
- Remove placeholder TODOs that are now addressed

### Step 7: Update Package Init

**File**: `src/node_agent/__init__.py`

Export the app factory and any public types.

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/node_agent/dependencies.py` | DI providers |
| `src/node_agent/lifespan.py` | Lifecycle management |
| `src/node_agent/routes/__init__.py` | Routes package init |
| `src/node_agent/routes/health.py` | Health endpoint |
| `src/node_agent/routes/operations.py` | Operation stubs |
| `src/node_agent/models.py` | Node-specific Pydantic models |

## Files to Modify

| File | Changes |
|------|---------|
| `src/node_agent/main.py` | Refactor to use app factory, add entry point |
| `src/node_agent/__init__.py` | Export public API |

---

## Validation Plan

### Static Validation

1. **Import check**: All new modules import without errors
   ```bash
   python -c "from src.node_agent import main; print('OK')"
   ```

2. **Type check**: Run mypy on new files (if available)
   ```bash
   python -m mypy src/node_agent --ignore-missing-imports
   ```

3. **Lint check**: Run ruff on new and modified files
   ```bash
   ruff check src/node_agent/
   ```

### Runtime Validation

1. **App creation**: Verify FastAPI app instantiates
   ```bash
   python -c "from src.node_agent.main import create_app; app = create_app(); print(app.title)"
   ```

2. **Health endpoint**: Verify endpoint responds
   ```bash
   # Start server in background, then:
   curl -s http://localhost:8080/health | python -m json.tool
   ```

3. **Config validation**: Verify config loading works
   ```bash
   python -c "from src.node_agent.config import get_node_agent_config; c = get_node_agent_config(); print(c.node_name)"
   ```

### Acceptance Criteria Verification

| Criterion | Verification |
|-----------|--------------|
| Package shape defined | FastAPI app with routes exists and responds |
| Health endpoint explicit | `/health` returns schema-matching JSON |
| Executor boundary separate | Executor is in node_agent package, not hub |

---

## Integration Points

### With Shared Modules

- `src.shared.logging` - structured logging
- `src.shared.context` - trace ID propagation
- `src.shared.exceptions` - error handling

### With Future Tickets

- **CORE-004**: Hub-to-node client will call node agent `/health` for health checks
- **REPO-002**: Implement `list_directory`, `read_file` in executor
- **REPO-003**: Implement `search_files`, `git_status` in executor
- **WRITE-001**: Implement `write_file` in executor

---

## Risks and Assumptions

### Assumptions

1. Node agent runs on each managed machine with Python 3.11+
2. Tailscale provides network connectivity between hub and node agents
3. Allowed paths are configured at deployment time via environment
4. No multi-tenant access (single-operator deployment)

### Risks

| Risk | Mitigation |
|------|------------|
| Config validation fails at startup | Ensure env var defaults are sensible; log clear errors |
| Executor path validation too restrictive | Test with various path configurations |
| Health endpoint timeout under load | Keep health check lightweight (no DB calls) |

---

## Decision Blockers

None. All blocking decisions resolved:
- Config pattern already exists from SETUP-002
- Executor class already exists from SETUP-001
- Hub lifespan pattern available as reference
- Shared logging already integrated

---

## Summary

This plan creates a complete node-agent service skeleton with:
- FastAPI app with proper lifecycle
- Health endpoint for hub polling
- Bounded executor integration
- Structured logging
- Clear separation from hub code

The node agent will be ready for CORE-004 (hub-to-node connectivity) and subsequent repo operation implementations.
