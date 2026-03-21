# Implementation Summary: FIX-003 - Fix hub MCP router async wiring and circular import

## Changes Made

### 1. Created `src/hub/handlers.py` (new file)
- Holds the shared `mcp_handler` instance
- Breaks the circular import dependency between main.py and routes.py

### 2. Modified `src/hub/main.py`
- Removed local `mcp_handler` definition
- Now imports `mcp_handler` from `handlers.py`
- Kept single `/health` endpoint

### 3. Modified `src/hub/routes.py`
- Changed import from `from src.hub.main import mcp_handler` to `from src.hub.handlers import mcp_handler`
- Removed duplicate `/health` endpoint

### 4. Modified `src/hub/mcp.py`
- Changed `_ensure_router()` from synchronous to async method
- Removed problematic event loop detection code
- Now properly uses `await get_policy_engine()` instead of trying to run sync code in async context

## Resolution Summary

| Issue | Status |
|-------|--------|
| Circular import main.py ↔ routes.py | ✅ Resolved - handlers.py breaks the cycle |
| `_ensure_router()` async issue | ✅ Resolved - method is now async and uses await properly |
| Duplicate /health endpoints | ✅ Resolved - removed from routes.py |

## Acceptance Criteria Status

- [ ] MCP endpoints respond correctly in async FastAPI context
- [ ] No circular import between main.py and routes.py
- [ ] Single /health endpoint definition
- [ ] `python3 -c 'from src.hub.main import app'` succeeds (import chain fixed)
