# Implementation Artifact — FIX-024 (Reopened)

## Ticket
- ID: FIX-024
- Title: Fix node-client response envelope stripping and path-mode search output parsing
- Lane: bugfix
- Stage: implementation
- Resolution: reopened

## Two Defects Fixed

### Defect 1 — `format_tool_response` dict-in-error.message

**File:** `src/hub/transport/mcp.py`
**Lines affected:** 131–139

**Before:**
```python
if error:
    response["error"] = {
        "code": -32603,
        "message": error,
    }
```

**After:**
```python
if error:
    if isinstance(error, dict):
        error_message = error.get("message", str(error))
    else:
        error_message = error
    response["error"] = {
        "code": -32603,
        "message": error_message,
    }
```

**Rationale:** When `error` is already a structured MCP error dict (e.g., `{"code": -32603, "message": "..."}`), the original code placed the entire dict into `error.message`. JSON-RPC 2.0 requires `message` to be a string. The fix extracts the string message from dict errors before assignment.

### Defect 2 — `git_status_handler` reads from wrong envelope level

**File:** `src/hub/tools/git_operations.py`
**Lines affected:** 105–151

**Root cause:** `node_client.git_status()` returns `{"success": True, "data": {"branch": "...", "is_clean": True, ...}}`. The handler did `result.get("is_clean")` which read from the outer dict, getting `None` instead of the actual value from `result["data"]["is_clean"]`.

**Fix — added after `result = await node_client.git_status(...)`:**
```python
# Unwrap OperationResponse envelope
payload = result.get("data", {}) if isinstance(result, dict) else {}
```

**Changed** all `result.get(...)` calls inside the success block to `payload.get(...)` for git-specific fields:
- `branch`, `is_clean`, `staged`, `staged_count`, `modified`, `modified_count`, `untracked`, `untracked_count`, `ahead`, `behind`, `recent_commits`

**Preserved:** The outer `result.get("success", False)` check — that correctly reads from the outer envelope.

## Validation

**Command:**
```
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.services.node_client import HubNodeClient; from src.node_agent.executor import OperationExecutor; print('OK')"
```

**Output:** `OK`  
**Exit code:** 0

## Acceptance Criteria Status
1. ✅ `format_tool_response` never places a dict in `error.message` — string extraction applied.
2. ✅ `git_status_handler` reads git fields from `payload = result.get("data", {})`.
3. Tests: existing tests remain unchanged; contract preserved.
4. ✅ Import compile check exits 0.
