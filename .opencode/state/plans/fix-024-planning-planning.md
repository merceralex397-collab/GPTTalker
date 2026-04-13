# Planning Artifact — FIX-024 (Reopened)

## Ticket
- ID: FIX-024
- Title: Fix node-client response envelope stripping and path-mode search output parsing
- Lane: bugfix
- Stage: planning
- Resolution: reopened (post-completion defect)

## Defects to Fix

### Defect 1 — `format_tool_response` places dict inside `error.message`

**File:** `src/hub/transport/mcp.py`
**Function:** `format_tool_response`

**Problem:** When `error` argument is already a structured MCP error dict (e.g., `{"code": -32603, "message": "..."}`), the code does:
```python
response["error"] = {
    "code": -32603,
    "message": error,   # error is a dict, not a string!
}
```
This violates JSON-RPC 2.0 which requires `error.message` to be a string.

**Fix:** Before assigning, check if `error` is a dict and extract the string message:
```python
if error:
    if isinstance(error, dict):
        error_message = error.get("message", str(error))
    else:
        error_message = error
    response["error"] = {"code": -32603, "message": error_message}
```

### Defect 2 — `git_operations.py` reads git status fields from wrong envelope level

**File:** `src/hub/tools/git_operations.py`
**Function:** `git_status_handler`

**Problem:** `node_client.git_status()` returns the full `OperationResponse` envelope:
```python
# node_client.git_status returns:
{"success": True, "data": {"branch": "...", "is_clean": True, ...}}
```

But the handler reads fields directly from the outer envelope:
```python
result = await node_client.git_status(...)
if result.get("success", False):
    is_clean = result.get("is_clean", False)        # WRONG — reads from outer, not data
    staged_count = result.get("staged_count", 0)     # WRONG
    branch = result.get("branch", "unknown")          # WRONG
```

This means `result.get("is_clean")` looks in `{"success": True, "data": {...}}` and gets `None`, not the actual git status value.

**Fix:** Unwrap the envelope with `payload = result.get("data", {})` before reading git-specific fields:
```python
result = await node_client.git_status(...)
payload = result.get("data", {}) if isinstance(result, dict) else {}
if result.get("success", False):
    is_clean = payload.get("is_clean", False)
    staged_count = payload.get("staged_count", 0)
    ...
```

## Implementation Steps

1. Fix `format_tool_response` in `src/hub/transport/mcp.py` to extract string message from dict `error`.
2. Fix `git_status_handler` in `src/hub/tools/git_operations.py` to unwrap `OperationResponse` envelope before reading fields.
3. Validate with import compile check.
4. QA verification via code inspection of both fixes.

## Acceptance Criteria
1. `format_tool_response` never places a dict inside `error.message` — string extraction is applied.
2. `git_status_handler` correctly reads branch/is_clean/staged/modified/untracked/ahead/behind/recent_commits from `payload = result.get("data", {})`.
3. Existing tests for these operations pass or are updated to match actual production contract.
4. Import compile check exits 0.

## Files to Modify
- `src/hub/transport/mcp.py` — `format_tool_response` function
- `src/hub/tools/git_operations.py` — `git_status_handler` function
