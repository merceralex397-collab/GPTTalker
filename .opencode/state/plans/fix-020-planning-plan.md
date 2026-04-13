# Plan for FIX-020: Fix missing authentication enforcement on node agent operational routes

## Current Code Status

After thorough code inspection of the current codebase, the following is the status of all 7 production defects:

| # | Defect | Status | Evidence |
|---|-------|--------|----------|
| 1 | Auth on node agent operational routes | ✅ ALREADY FIXED | All 5 routes have `require_api_key` dependency (operations.py lines 76, 139, 197, 274, 333) |
| 2 | SearchRequest.mode field | ✅ ALREADY FIXED | `mode: str = "text"` present at operations.py line 45 |
| 3 | HubNodeClient.read_file HTTP method | ✅ ALREADY FIXED | Uses POST `/operations/read-file` with JSON body (node_client.py lines 199-204) |
| 4 | Policy router failure reporting | ✅ ALREADY CORRECT | Returns `{"success": False, "error": str(e)}` on exception (policy_router.py lines 503-512) |
| 5 | MCP error wrapping double-wrapping | ⚠️ NEEDS FIX | See analysis below |
| 6 | Port wiring for node agent calls | ✅ NO BUG | Default HTTP port assumed; node agents run on port 80/8000 |
| 7 | Search parsing in path mode | ✅ ALREADY CORRECT | Parser handles `--files-with-matches` output via fallback (executor.py lines 258-263) |

---

## Defect 5 Analysis: MCP Error Double-Wrapping

### Root Cause

The MCP transport layer (`src/hub/transport/mcp.py`) and the policy router (`src/hub/tool_routing/policy_router.py`) have misaligned error contracts:

**Policy router error output** (policy_router.py `_execute_handler`):
```python
# Lines 503-512
return {
    "success": False,
    "error": str(e),
}
```

**MCP transport** (`format_tool_response`):
```python
# Lines 131-135: error path
if error:
    response["error"] = {
        "code": -32603,
        "message": error,
    }

# Lines 136-149: success path wraps result under "data"
else:
    if isinstance(result, dict) and "data" in result:
        response["result"] = {
            "success": result.get("success", True),
            "data": result["data"],
            "duration_ms": duration_ms,
        }
```

### Problem

When a handler returns `{"success": False, "error": "some message"}`:
1. `format_tool_response` sees no `error` parameter passed (it's only passed by caller)
2. It goes to the success path and wraps the dict under `result.data`
3. Result: `{"jsonrpc": "2.0", "result": {"success": False, "data": {"success": False, "error": "..."}}}`
4. The inner `{"success": False, "error": "..."}` is buried inside `result.data` instead of being at `response["error"]`

When the caller passes an explicit `error` string (rare path):
1. The error gets hardcoded as `{"code": -32603, "message": error}`
2. But `format_policy_error` already provides a proper JSON-RPC 2.0 error at `response["error"]`
3. This could cause double-wrapping if both paths are hit

### Fix Approach

The fix is to detect handler-returned error dicts (`{"success": False, "error": "..."}`) and promote them to the transport-level error response:

**File to change:** `src/hub/transport/mcp.py`

**Change in `format_tool_response`:**
```python
# Before the success-path handling, check if result contains a handler-level error
if isinstance(result, dict) and result.get("success") is False and "error" in result:
    # Handler returned an error - promote to transport-level error
    response["error"] = {
        "code": -32603,
        "message": result.get("error", "Unknown error"),
    }
    return response
```

This ensures:
1. Handler errors (`{"success": False, "error": "..."}`) become proper JSON-RPC 2.0 errors at `response["error"]`
2. Proper successes (`{"success": True, "data": ...}`) work as before
3. No double-wrapping occurs

---

## Acceptance Criteria

1. **Defect 1-4, 6-7**: No action needed — already fixed/correct in current code
2. **Defect 5**: After the fix, handler-returned errors (`{"success": False, "error": "..."}`) are promoted to transport-level JSON-RPC 2.0 error format at `response["error"]`
3. **Verification**: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.transport.mcp import format_tool_response; print('OK')"` exits 0
4. **No regression**: Existing happy-path tool responses still work correctly

---

## Implementation

### File: `src/hub/transport/mcp.py`

**Function:** `format_tool_response`

**Location:** After line 130 (`if error:` block ends at line 135), insert error promotion check before the success path handling.

**New code block to add:**
```python
    # Promote handler-returned errors to transport-level JSON-RPC errors
    if isinstance(result, dict) and result.get("success") is False and "error" in result:
        response["error"] = {
            "code": -32603,
            "message": result.get("error", "Unknown error"),
        }
        return response
```

**Rationale:** This check runs before the success-path handling so handler errors are caught first. The check is specific enough (`success is False`) to avoid false positives on happy-path responses that happen to have a `success` field.

---

## Validation Plan

1. **Import test**: `python -c "from src.hub.transport.mcp import format_tool_response"`
2. **Unit test for error promotion**: Create a focused test that calls `format_tool_response` with a handler error dict `{"success": False, "error": "permission denied"}` and verify the output is `{"jsonrpc": "2.0", "error": {"code": -32603, "message": "permission denied"}}`
3. **Unit test for happy path**: Verify normal responses still work: `format_tool_response({"success": True, "data": {"foo": "bar"}})` produces `{"jsonrpc": "2.0", "result": {"success": True, "data": {"foo": "bar"}, "duration_ms": 0}}`

---

## Files Modified

| File | Change |
|------|--------|
| `src/hub/transport/mcp.py` | Add handler error promotion in `format_tool_response` |

---

## Summary

FIX-020 is largely already resolved in the current codebase. The only defect requiring code change is **Defect 5 (MCP error wrapping)**, which needs a minor fix in `src/hub/transport/mcp.py` to promote handler-returned error dicts to proper JSON-RPC 2.0 transport errors. This prevents errors from being buried inside `result.data` and ensures clients receive properly formatted error responses.
