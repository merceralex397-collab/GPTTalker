# Implementation Plan: SETUP-004 - FastAPI Hub App Shell and MCP Transport Baseline

## 1. Scope

This ticket creates the initial FastAPI application shell for the GPTTalker hub, including:
- Complete FastAPI app with startup/shutdown lifecycle
- Dependency injection system for database, config, and logging
- MCP transport layer with tool handler primitives
- Route organization with MCP tool routing endpoints
- Health check and basic observability endpoints

**Acceptance Criteria:**
1. Hub app entrypoint and package shape are defined
2. MCP-facing transport boundary is explicit
3. Startup path leaves room for policy and registry injection

---

## 2. Files and Systems Affected

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `src/hub/dependencies.py` | Dependency injection providers for database, config, logging |
| `src/hub/lifespan.py` | App lifecycle management (startup/shutdown) |
| `src/hub/transport/__init__.py` | Transport layer package init |
| `src/hub/transport/base.py` | Base transport protocol classes |
| `src/hub/transport/mcp.py` | MCP protocol transport implementation |
| `src/hub/tool_router.py` | Tool routing and registry primitives |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `src/hub/main.py` | Complete with lifespan, CORS, dependency injection setup |
| `src/hub/mcp.py` | Implement MCP tool handler stub with proper structure |
| `src/hub/routes.py` | Add MCP endpoint routes |
| `src/shared/schemas.py` | Add MCP-specific request/response schemas if needed |

### Dependencies

All required dependencies are already in `pyproject.toml`:
- `fastapi>=0.109.0`
- `uvicorn[standard]>=0.27.0`
- `aiosqlite>=0.19.0`
- `httpx>=0.26.0`
- `pydantic>=2.5.0`
- `pydantic-settings>=2.1.0`

---

## 3. Implementation Steps

### Step 1: Create Dependency Injection Module (`src/hub/dependencies.py`)

Create dependency providers that FastAPI can inject:

```python
# Key dependencies to provide:
# - get_db() -> AsyncGenerator[aiosqlite.Connection]
# - get_config() -> HubConfig
# - get_logger() -> logging.Logger
# - get_trace_id() -> str
```

**Implementation Details:**
- Use `fastapi.Depends` pattern
- Connect to the shared `DatabaseManager` from `src.shared.database`
- Use hub-specific config from `src.hub.config`
- Ensure dependencies are request-scoped with proper cleanup

### Step 2: Create Lifespan Management (`src/hub/lifespan.py`)

Define the app lifecycle with proper startup/shutdown:

```python
# Lifespan tasks:
# 1. Initialize logging from config
# 2. Initialize database connection
# 3. Run migrations (from SETUP-003)
# 4. Log startup completion
# 5. On shutdown: close database, log shutdown
```

**Implementation Details:**
- Use `contextlib.asynccontextmanager` with FastAPI's lifespan
- Return connection/database to dependency injection system
- Handle graceful shutdown with proper cleanup

### Step 3: Complete FastAPI App (`src/hub/main.py`)

Enhance the existing stub with:

```python
# Enhancements:
# 1. Import and integrate lifespan from lifespan.py
# 2. Add CORS middleware (allow specific origins configurable)
# 3. Register exception handlers from src.shared.middleware
# 4. Include router from routes.py
# 5. Configure lifespan events
```

**CORS Configuration:**
- Default: Allow all (for development)
- Configurable via environment: `GPTTALKER_CORS_ORIGINS`
- Use `fastapi.middleware.cors.CORSMiddleware`

### Step 4: Create MCP Transport Layer

Create `src/hub/transport/base.py`:
```python
# Base classes:
# - TransportProtocol: Abstract base for transport implementations
# - TransportResult: Standardized transport result wrapper
# - TransportError: Exception for transport-level errors
```

Create `src/hub/transport/mcp.py`:
```python
# MCP-specific transport:
# - MCPTransport: Handles MCP protocol framing
# - MCPMessage: MCP message model (request/response)
# - parse_tool_call(): Parse MCP tool invocation
# - format_tool_response(): Format tool result for MCP
```

### Step 5: Create Tool Router (`src/hub/tool_router.py`)

Define tool routing primitives:

```python
# Components:
# - ToolRegistry: Maps tool names to handler functions
# - ToolRouter: Routes tool calls to appropriate handlers
# - register_tool(): Decorator/function to register tool handlers
# - get_tool_schema(): Get tool parameter schema
```

**Integration Point:**
- Leave room for CORE-005 (policy engine) to inject validation
- Leave room for CORE-006 to add full routing logic
- This is a *baseline* - full implementation comes later

### Step 6: Complete MCP Handler (`src/hub/mcp.py`)

Refactor the stub to use the new transport layer:

```python
# Enhancements:
# 1. Import and use MCPTransport
# 2. Add proper initialization with dependencies
# 3. Create handle_tool_call() that:
#    - Validates tool name
#    - Routes to registered handler
#    - Formats response in MCP format
#    - Handles errors gracefully
```

### Step 7: Add MCP Routes (`src/hub/routes.py`)

Add the MCP-facing endpoints:

```python
# Endpoints to add:
# POST /mcp/v1/tools/call - Execute a tool
# GET  /mcp/v1/tools       - List available tools
# GET  /mcp/v1/health     - MCP-specific health check
```

**MCP Endpoint Models:**
```python
# MCPToolCallRequest:
#   - tool_name: str
#   - parameters: dict
#   - trace_id: str (optional, generated if missing)

# MCPToolCallResponse:
#   - success: bool
#   - result: Any
#   - error: str | None
#   - trace_id: str
#   - duration_ms: int
```

### Step 8: Update Health Check (`src/hub/main.py` existing)

Enhance the existing health check to be more comprehensive:

```python
# Health check should verify:
# 1. App is running (existing)
# 2. Database is accessible
# 3. Return config-redacted status
```

---

## 4. Validation Plan

### Validation Commands

```bash
# Lint check
ruff check src/hub/

# Type check (if mypy configured)
ruff check src/hub/ --select=type

# Import check - verify all modules load
python -c "from src.hub.main import app; print('App loads OK')"

# Test that dependencies resolve
python -c "
import asyncio
from src.hub.lifespan import lifespan
from src.hub.dependencies import get_db, get_config, get_logger
print('Dependencies import OK')
"

# Verify routes registered
python -c "
from src.hub.main import app
routes = [r.path for r in app.routes]
assert '/health' in routes
assert '/mcp/v1/tools' in routes
assert '/mcp/v1/tools/call' in routes
print('Routes registered OK')
"

# Run any existing tests
pytest tests/ -v --tb=short
```

### Success Criteria

| Criterion | Verification |
|-----------|--------------|
| App loads without errors | `python -c "from src.hub.main import app"` succeeds |
| Health endpoint responds | `curl http://localhost:8000/health` returns 200 |
| MCP endpoints exist | Routes `/mcp/v1/tools` and `/mcp/v1/tools/call` registered |
| Dependencies inject correctly | FastAPI dependency override test passes |
| Database initializes on startup | Lifespan runs without errors |
| CORS middleware configured | Middleware stack includes CORS |
| Exception handlers wired | Errors return structured JSON |
| Tool registry structure exists | `ToolRegistry` class can be instantiated |

---

## 5. Risks and Assumptions

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database not initialized before routes | Runtime errors | Lifespan ensures initialization before serving |
| Circular imports | Development blockers | Use lazy imports in transport layer |
| MCP protocol not fully defined | May need rework | Build extensible transport, not protocol-specific |

### Assumptions

| Assumption | Notes |
|------------|-------|
| SETUP-001 src/hub structure is correct | Uses existing package layout |
| SETUP-002 shared modules work | Database, config, logging available |
| SETUP-003 database layer is ready | Repositories and migrations exist |
| FastAPI 0.109+ lifespan API stable | Uses documented asynccontextmanager pattern |

---

## 6. Blockers and Required User Decisions

### Blockers

**None** - All dependencies resolved from previous tickets:
- SETUP-001 provides `src/hub/` structure
- SETUP-002 provides shared schemas, config, logging, middleware
- SETUP-003 provides database layer with migrations

### Required Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| CORS origins | Allow all vs. specific | Default allow-all, env-configurable |
| MCP transport binding | HTTP vs. WebSocket | Start with HTTP, WebSocket deferred |
| Tool handler pattern | Class-based vs. functions | Functions with dependency injection |

---

## 7. Integration Points for Future Tickets

This implementation deliberately leaves hooks for:

| Future Ticket | Integration Point |
|---------------|-------------------|
| CORE-001 | Node registry injected via dependencies |
| CORE-002 | Repo/write-target/LLM registries via dependencies |
| CORE-005 | Policy engine validation before tool execution |
| CORE-006 | Full tool routing in `tool_router.py` |
| REPO-001+ | Tool handlers registered via `ToolRegistry` |
| EDGE-001 | Cloudflare Tunnel hooks in lifespan/startup |

---

## 8. Summary

This ticket establishes the foundational FastAPI shell for the GPTTalker hub:

1. **App Shell** - Complete FastAPI app with proper lifecycle, CORS, and health checks
2. **Dependency Injection** - Providers for database, config, logging ready for FastAPI
3. **MCP Transport** - Extensible transport layer with MCP protocol primitives
4. **Tool Routing** - Registry and routing structure ready for tool handlers
5. **HTTP Endpoints** - MCP-facing endpoints at `/mcp/v1/...`

The implementation is intentionally minimal - it provides the *baseline* structure that CORE tickets will flesh out with actual tool implementations, policy enforcement, and node connectivity.
