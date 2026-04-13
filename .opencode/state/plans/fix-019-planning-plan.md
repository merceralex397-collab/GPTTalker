# FIX-019: Fix MCP tools endpoint returning empty list

## Root Cause Analysis

**Problem**: The MCP tools endpoint (`GET /mcp/v1/tools`) returns an empty list because tool registration never runs.

**Technical Details**:

1. **Deprecated Pattern Conflict**: `src/hub/main.py` (line 38) creates the FastAPI app with `lifespan=lifespan`, which is the modern FastAPI lifespan context manager pattern.

2. **Orphaned Startup Handler**: Lines 57-64 in `main.py` use the deprecated `@app.on_event("startup")` decorator to call `register_all_tools(registry)`.

3. **FastAPI Behavior**: When `lifespan=` parameter is set on a FastAPI app, the `@app.on_event("startup")` handler is **deprecated and may not fire**. This is documented FastAPI behavior - the lifespan context manager takes over lifecycle management and the old event-based handlers are ignored.

4. **Missing Registration in Lifespan**: `src/hub/lifespan.py` step 8 (lines 123-129) calls `mcp_handler.initialize(app)`, which builds the `PolicyAwareToolRouter` and populates it with services, but it **never calls `register_all_tools()`**.

5. **Registry Without Tools**: The `MCPProtocolHandler.initialize()` method (mcp.py lines 39-238) gets the global registry via `get_global_registry()` (line 53) but only uses it to build the router. The tools are never registered, so `list_tools()` returns empty.

**Evidence**:
- `main.py:38`: `app = FastAPI(..., lifespan=lifespan)`
- `main.py:57-64`: `@app.on_event("startup")` handler - **DEPRECATED when lifespan= is set**
- `lifespan.py:127-129`: `mcp_handler.initialize(app)` - does NOT call `register_all_tools`
- `mcp.py:53`: `registry = get_global_registry()` - registry obtained but tools never registered
- `tools/__init__.py:507-522`: `register_all_tools()` function exists but is never called from lifespan

---

## Implementation Steps

### Step 1: Add tool registration to lifespan (lifespan.py)

**File**: `src/hub/lifespan.py`

**Change**: Insert tool registration as a new step (step 8a) BEFORE the existing `mcp_handler.initialize(app)` call at line 129.

**Location**: Between lines 122 and 127 (after tunnel manager startup, before MCP router initialization)

**New code**:
```python
# Step 8a: Register all MCP tools BEFORE initializing MCP handler
# Note: This must happen here because @app.on_event("startup") in main.py
# is deprecated when lifespan= is set. Tools must be registered before
# mcp_handler.initialize() builds the router.
from src.hub.tool_router import get_global_registry
from src.hub.tools import register_all_tools

registry = get_global_registry()
register_all_tools(registry)
logger.info("mcp_tools_registered", tool_count=registry.tool_count)
```

**Rationale**: Tools must be registered on the registry BEFORE `mcp_handler.initialize(app)` is called, because `initialize()` passes the registry to `PolicyAwareToolRouter`. If tools are not registered before initialization, the router will have an empty registry.

### Step 2: Remove orphaned startup handler (main.py)

**File**: `src/hub/main.py`

**Change**: Remove lines 57-64 (the entire `@app.on_event("startup")` handler).

**Before**:
```python
@app.on_event("startup")
async def register_tools():
    """Register MCP tools on application startup."""
    from src.hub.tools import register_all_tools

    registry = get_global_registry()
    register_all_tools(registry)
    logger.info("tools_registered", tool_count=registry.tool_count)
```

**After**: Delete these lines entirely.

**Rationale**: This handler is deprecated and does not fire when `lifespan=` is set. Removing it eliminates dead code and prevents confusion.

---

## Validation Plan

### Acceptance Criteria

| # | Criterion | Verification Method |
|---|---|-----------|
| 1 | Register all MCP tools during lifespan startup instead of deprecated @app.on_event('startup') | Code inspection: lifespan.py contains `register_all_tools()` call before `mcp_handler.initialize()` |
| 2 | GET /mcp/v1/tools returns all registered tools | Runtime test: curl or test client calls `/mcp/v1/tools` and verifies non-empty list |
| 3 | No orphaned @app.on_event('startup') handlers remain in main.py | Code inspection: main.py contains no `@app.on_event` decorators |
| 4 | `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"` exits 0 | Import test: verifies no import errors introduced |

### Validation Commands

```bash
# 1. Import test - verify no syntax/import errors
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"

# 2. Lint check - verify no new lint issues
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/main.py src/hub/lifespan.py

# 3. Smoke test - runtime verification of tool registration
# (requires hub to be runnable - may be blocked by external dependencies like database/qdrant)
```

### Files Modified

| File | Change Type | Lines Affected |
|------|-----------|---------------|
| `src/hub/lifespan.py` | Add step 8a | Insert ~7 lines before line 127 |
| `src/hub/main.py` | Remove deprecated handler | Delete lines 57-64 |

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Import ordering in lifespan.py | Low | The import `from src.hub.tools import register_all_tools` is inside the lifespan function to avoid potential circular imports at module load time, consistent with other imports in the file |
| Timing dependency | Low | Tools must be registered before `initialize()` - the fix places registration immediately before the `initialize()` call in the same step sequence |
| Backward compatibility | None | The old `@app.on_event("startup")` handler was never working (deprecated), so removing it has no functional impact |

---

## Dependencies and Prerequisites

- **No new dependencies**: The fix uses only existing imports (`get_global_registry`, `register_all_tools`)
- **No migrations needed**: Database schema is unaffected
- **No configuration changes**: Environment variables or config files unchanged
- **No test changes required**: Existing tests should pass after fix

---

## Implementation Order

1. **Modify `src/hub/lifespan.py`**: Add tool registration step before `mcp_handler.initialize(app)`
2. **Modify `src/hub/main.py`**: Remove the deprecated `@app.on_event("startup")` handler
3. **Run validation**: Execute import test and lint checks
4. **Register planning artifact**: Record the plan in the artifact registry