# Code Review for FIX-003

## Summary

Review of implementation to fix three hub wiring issues:
1. Circular import between main.py and routes.py
2. `_ensure_router()` synchronous method called from async context  
3. Duplicate `/health` endpoints

## Changes Reviewed

### New File: `src/hub/handlers.py`
- Holds shared `mcp_handler` instance
- Breaks circular import dependency
- Clean, minimal implementation

### Modified: `src/hub/main.py`
- Imports `mcp_handler` from handlers.py instead of defining locally
- Removed unused import
- Single `/health` endpoint preserved

### Modified: `src/hub/routes.py`
- Imports `mcp_handler` from handlers.py instead of main.py
- Removed duplicate `/health` endpoint

### Modified: `src/hub/mcp.py`
- Changed `_ensure_router()` from sync to async method
- Removed problematic event loop detection code
- Now properly uses `await get_policy_engine()`
- Updated callers to await the method

## Decision

**APPROVED** - All three issues are fixed correctly:
- Circular import resolved via handlers.py
- Async method now properly awaits instead of trying sync event loop operations
- Duplicate health endpoint removed

## Verification Checklist

- [x] No circular import in new import chain
- [x] `_ensure_router()` is now async and uses await
- [x] Single /health endpoint in main.py
- [x] Code compiles (no syntax errors visible)
- [x] Import chain forms linear path: main → routes → handlers → mcp
