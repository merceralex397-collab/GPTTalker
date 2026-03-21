# Implementation Plan: FIX-003 - Fix hub MCP router async wiring and circular import

## Ticket Summary

Three related hub wiring issues:
1. `MCPProtocolHandler._ensure_router()` fails in async context
2. Circular import between `main.py` and `routes.py`
3. Duplicate `/health` endpoints in `main.py` and `routes.py`

## Issue Analysis

### Issue 1: Async context problem in _ensure_router()
**Location**: `src/hub/mcp.py`, lines 32-68

The `_ensure_router()` method is synchronous but called from async methods. It tries to get an event loop and run `get_policy_engine()` synchronously, which fails when the loop is already running (FastAPI async context).

### Issue 2: Circular import
**Location**: `src/hub/main.py` and `src/hub/routes.py`

- `main.py` imports `from src.hub.routes import router` (line 9)
- `routes.py` imports `from src.hub.main import mcp_handler` (line 10)

This creates a circular dependency.

### Issue 3: Duplicate /health endpoints
**Locations**:
- `main.py:68` - `@app.get("/health")`
- `routes.py:47` - `@router.get("/health")`

Both define `/health` endpoint, causing a conflict when router is included.

## Proposed Fix

### Fix 1: Make _ensure_router async-compatible
Change `_ensure_router()` to be an async method or pass the router via dependency injection instead of lazy initialization.

### Fix 2: Break circular import
Move `mcp_handler` creation to a separate module or use lazy import inside the function.

### Fix 3: Remove duplicate health endpoint
Keep only one `/health` endpoint - remove the one in `routes.py` since `main.py` already has one.

## Implementation Steps

1. **Fix circular import**:
   - Create `src/hub/handlers.py` to hold `mcp_handler` instance
   - Update `routes.py` to import from `handlers.py` instead of `main.py`
   - Update `main.py` to import `mcp_handler` from `handlers.py`

2. **Fix async _ensure_router**:
   - Change `_ensure_router()` to accept router as parameter
   - Or make it an async method
   - Or inject router via FastAPI dependency injection

3. **Remove duplicate /health endpoint**:
   - Remove `@router.get("/health")` from `routes.py`
   - Keep `@app.get("/health")` in `main.py`

4. **Verify**: `python3 -c 'from src.hub.main import app'` succeeds

## Acceptance Criteria

- [ ] MCP endpoints respond correctly in async FastAPI context
- [ ] No circular import between main.py and routes.py
- [ ] Single /health endpoint definition
- [ ] `python3 -c 'from src.hub.main import app'` succeeds

## Risk Assessment

- **Risk level**: Medium
- **Impact**: Fixes blocking hub startup issues
- **Mitigation**: Careful import restructuring, no behavioral changes

## Dependencies

FIX-001 (walrus operator fix) - already completed
