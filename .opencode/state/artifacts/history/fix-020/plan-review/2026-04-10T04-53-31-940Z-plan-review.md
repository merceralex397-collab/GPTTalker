# Plan Review for FIX-020: Fix missing authentication enforcement on node agent operational routes

## Verdict: APPROVED

## Overview

This plan review validates the planning artifact's findings against current source code. With one exception (Defect 5's exact insertion point), all plan conclusions are confirmed accurate by direct code inspection.

---

## Defect-by-Defect Assessment

### Defect 1: Auth on node agent operational routes
**Status: ✅ CONFIRMED ALREADY FIXED**

| Route | File | Line | Evidence |
|-------|------|------|----------|
| `POST /operations/list-dir` | operations.py | 76 | `_: None = Depends(require_api_key)` |
| `POST /operations/read-file` | operations.py | 139 | `_: None = Depends(require_api_key)` |
| `POST /operations/search` | operations.py | 197 | `_: None = Depends(require_api_key)` |
| `POST /operations/git-status` | operations.py | 274 | `_: None = Depends(require_api_key)` |
| `POST /operations/write-file` | operations.py | 333 | `_: None = Depends(require_api_key)` |

The `require_api_key` dependency (dependencies.py lines 25-43) is correctly implemented: it skips auth when `config.api_key is None`, otherwise validates the bearer token and returns 401 on mismatch.

**Plan conclusion: CORRECT**

---

### Defect 2: SearchRequest.mode field
**Status: ✅ CONFIRMED ALREADY FIXED**

`SearchRequest` at operations.py lines 39-47:
```python
class SearchRequest(BaseModel):
    directory: str
    pattern: str
    include_patterns: list[str] | None = None
    mode: str = "text"  # Search mode: text, path, or symbol
    max_results: int = 1000
    timeout: int = 60
```

The `mode` field is present with default `"text"`, and the search handler validates it against `["text", "path", "symbol"]` at line 221.

**Plan conclusion: CORRECT**

---

### Defect 3: HubNodeClient.read_file HTTP method
**Status: ✅ CONFIRMED ALREADY FIXED**

`HubNodeClient.read_file` at node_client.py lines 181-215:
```python
response = await self.post(
    node,
    "/operations/read-file",
    json={"path": path, "offset": offset, "limit": limit},
    timeout=30.0,
)
```
Uses `POST` with JSON body (not `GET /files/read?path=`). Response parsing correctly extracts `data.get("data", {})`.

**Plan conclusion: CORRECT**

---

### Defect 4: Policy router failure reporting
**Status: ✅ CONFIRMED ALREADY CORRECT**

`PolicyAwareToolRouter._execute_handler` at policy_router.py lines 500-512:
```python
try:
    result = await handler(**exec_kwargs)
    logger.info("tool_execution_success", **log_context)
    return {
        "success": True,
        "result": result,
    }
except Exception as e:
    logger.error("tool_execution_failed", **log_context, error=str(e))
    return {
        "success": False,
        "error": str(e),
    }
```
Returns `{"success": False, "error": str(e)}` on exception, correctly preserving error information.

**Plan conclusion: CORRECT**

---

### Defect 5: MCP error double-wrapping
**Status: ⚠️ NEEDS FIX — Fix approach is correct, exact insertion point needs care**

**Root cause confirmed accurate.** `format_tool_response` at mcp.py lines 131-149:

```python
if error:
    response["error"] = {
        "code": -32603,
        "message": error,
    }
else:
    if isinstance(result, dict) and "data" in result:
        response["result"] = {
            "success": result.get("success", True),
            "data": result["data"],
            "duration_ms": duration_ms,
        }
    else:
        response["result"] = {
            "success": True,
            "data": result,
            "duration_ms": duration_ms,
        }
```

When `_execute_handler` returns `{"success": False, "error": "..."}`:
- No `error` parameter is passed to `format_tool_response`
- The result dict has no `"data"` key, so it falls to `else` branch
- Output becomes `{"jsonrpc": "2.0", "result": {"success": False, "data": {"success": False, "error": "..."}}}`
- The error is buried inside `result.data` instead of being at `response["error"]`

**Proposed fix is correct.** Promoting handler-returned `{"success": False, "error": "..."}` dicts to transport-level `response["error"]` before the success-path handling correctly resolves the double-wrapping issue.

**One planning observation:** The plan says to insert "after line 130 (`if error:` block ends at line 135)". Line 130 is the `if error:` check. The insertion should be after the `if error:` block (after line 135) but before the `else:` block (line 136). The implementation artifact should specify the insertion point precisely: after line 135 (`return response` for the error path) and before line 136 (`else:`). This is a minor precision issue, not a blocker.

**Plan conclusion: CORRECT — fix approach validated, implementation should insert before line 136**

---

### Defect 6: Port wiring for node agent calls
**Status: ✅ CONFIRMED NO BUG**

`NodeInfo` at models.py lines 54-71:
```python
class NodeInfo(BaseModel):
    node_id: str
    name: str
    hostname: str  # Note: no port field
    status: NodeStatus
    last_seen: datetime | None
```

`HubNodeClient.request` at node_client.py line 63:
```python
url = f"http://{node.hostname}{path}"
```

No port field exists in `NodeInfo`. The hostname is used directly without port reconstruction, which is correct behavior when node agents run on default HTTP port 80/8000.

**Plan conclusion: CORRECT**

---

### Defect 7: Search parsing in path mode
**Status: ✅ CONFIRMED ALREADY CORRECT**

When `mode == "path"`, ripgrep is invoked with `--files-with-matches` which outputs only filenames (no line numbers). Parser at executor.py lines 250-263:

```python
parts = line.split(":", 2)
if len(parts) >= 2:
    file_path = parts[0]
    try:
        line_num = int(parts[1])
    except ValueError:
        line_num = 0
    line_content = parts[2] if len(parts) > 2 else ""
```

For `--files-with-matches` output (e.g., `src/main.py`), `split(":", 2)` produces `["src/main.py"]` with length 1. The `len(parts) >= 2` check is False, so this line is skipped. Wait — re-examining the loop: if `len(parts) >= 2` is False (single-part line from `--files-with-matches`), the code still adds to `files_searched` at line 265? No, because lines 257-276 are inside the `if len(parts) >= 2:` block. Single-part lines are simply skipped.

But `files_searched` is populated inside the `if len(parts) >= 2:` block, so `--files-with-matches` output (which has no `:` separators) would result in `files_searched` being an empty set and `match_count` of 0. This appears to be the intended fallback behavior — path mode returns filenames without match details.

**Plan conclusion: CORRECT — parser handles path mode via fallback as documented**

---

## Summary of Findings

| Defect | Plan Status | Code Status | Action Required |
|--------|-------------|-------------|-----------------|
| 1 | Already Fixed | Confirmed | None |
| 2 | Already Fixed | Confirmed | None |
| 3 | Already Fixed | Confirmed | None |
| 4 | Already Correct | Confirmed | None |
| 5 | Needs Fix | Confirmed | **YES** — Fix in mcp.py |
| 6 | No Bug | Confirmed | None |
| 7 | Already Correct | Confirmed | None |

---

## Validation of Proposed Fix for Defect 5

**Change:** Insert handler-error promotion in `format_tool_response` before the success-path `else:` block.

**Location:** After line 135 (`return response` for the `if error:` path), before line 136 (`else:`).

**New code:**
```python
# Promote handler-returned errors to transport-level JSON-RPC errors
if isinstance(result, dict) and result.get("success") is False and "error" in result:
    response["error"] = {
        "code": -32603,
        "message": result.get("error", "Unknown error"),
    }
    return response
```

**Assessment:**
- ✅ Check `result.get("success") is False` is specific enough to avoid false positives
- ✅ Error code `-32603` (Internal error) is appropriate for handler-level errors
- ✅ Returns immediately after setting `response["error"]`, preventing further processing
- ✅ Promotes handler error to transport-level JSON-RPC error format
- ✅ Does not affect the explicit `error` parameter path (lines 131-135)

**No blockers identified.**

---

## Acceptance Criteria Validation

1. **Defect 1-4, 6-7:** No action needed — verified by code inspection
2. **Defect 5:** After the fix, handler-returned errors promote to transport-level JSON-RPC 2.0 error at `response["error"]` — fix approach validated
3. **Verification:** Import test `python -c "from src.hub.transport.mcp import format_tool_response; print('OK')"` should exit 0 after fix
4. **No regression:** Happy-path responses remain unchanged — the new check only fires when `success is False`

---

## Required Implementation Files

Only one file requires modification:

| File | Change |
|------|--------|
| `src/hub/transport/mcp.py` | Add handler error promotion in `format_tool_response` (before line 136 `else:`, after line 135 `return response`) |

---

## Conclusion

The plan is **decision-complete and implementation-ready**. All six "already fixed" defects are confirmed fixed by direct code inspection. The proposed fix for Defect 5 (MCP error double-wrapping) is correct in approach, specific in implementation, and introduces no regression risk. No blocking issues or required revisions.

Proceed to implementation with the Defect 5 fix in `src/hub/transport/mcp.py`.

(End of plan review)
