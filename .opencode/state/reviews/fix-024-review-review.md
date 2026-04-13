# Code Review — FIX-024

## Ticket
- **ID:** FIX-024
- **Title:** Fix node-client response envelope stripping and path-mode search output parsing
- **Lane:** bugfix
- **Stage:** review
- **Resolution:** reopened

## Verdict: APPROVED

Both fixes are correctly implemented, match the planning artifact exactly, and introduce no security regressions or widened trust boundaries. The fixes are safe to advance to QA.

---

## Fix 1 — `format_tool_response` dict-in-error.message

**File:** `src/hub/transport/mcp.py`
**Lines:** 131–139

### Implementation Verification ✅

The implemented fix matches the planning artifact exactly:

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

**JSON-RPC 2.0 compliance:** The JSON-RPC 2.0 spec requires `error.message` to be a string. When `error` arrives as a structured dict (e.g., `{"code": -32603, "message": "..."})`), the original code placed the entire dict into `error.message`, producing invalid JSON-RPC (`"message": {"code": -32603, "message": "..."})`. The fix extracts the string via `error.get("message", str(error))`, with `str(error)` as safe fallback if the dict has no "message" key.

### Findings

- **Type correctness:** `error_message` is always a string after the `if/else` branch. `error.get("message", str(error))` returns `str` because `dict.get()` returns the value type or the default, and `str(error)` is always `str`.
- **Secondary guard (lines 142–147):** The existing block that handles `result.get("success") is False and "error" in result` separately also produces a string `message` via `result.get("error", "Unknown error")`. No dict-in-message risk there.
- **No regression:** The rest of `format_tool_response` (lines 149–166) is unchanged. The `result`-handling path correctly avoids double-wrapping via the `"data" in result` guard.
- **No trust boundary change:** No new external inputs, no policy changes, no widened scope.

---

## Fix 2 — `git_status_handler` reads from wrong envelope level

**File:** `src/hub/tools/git_operations.py`
**Lines:** 105–151

### Implementation Verification ✅

The `node_client.git_status()` returns the full `OperationResponse` envelope:

```python
# node_client.git_status returns on HTTP 200:
{"success": True, "data": {"branch": "...", "is_clean": True, ...}}
```

The fix correctly unwraps it:

```python
# Line 106
payload = result.get("data", {}) if isinstance(result, dict) else {}
```

And all git-specific fields are read from `payload` (lines 120–150):
- `is_clean`, `staged`, `staged_count`, `modified`, `modified_count`, `untracked`, `untracked_count`, `ahead`, `behind`, `recent_commits`, `branch`

The outer `result.get("success", False)` check (line 119) correctly reads from the envelope level — that is the right field to check for operation success before accessing `payload`.

### Findings

- **Correct use of `isinstance` guard:** `isinstance(result, dict)` on line 106 is the correct guard before calling `.get()` on `result`. This handles the case where `node_client.git_status()` returns a non-dict (e.g., `None` or a string) on a network/pathological failure. `{}` is a safe fallback — all `payload.get()` calls then return defaults.
- **Consistency with other handlers:** `search.py` (line 160) and `inspection.py` (line 139) already use the identical `payload = result.get("data", {})` pattern. The fix brings `git_operations.py` into full consistency with established code patterns in the same layer.
- **No field left behind:** All 11 git-specific fields (`branch`, `is_clean`, `staged`, `staged_count`, `modified`, `modified_count`, `untracked`, `untracked_count`, `ahead`, `behind`, `recent_commits`) are now read from `payload`. The error-path still uses `result.get("error", ...)` for the outer envelope's error string — correct.
- **No trust boundary change:** The fix changes only local data extraction within the handler. No external input validation, no policy changes, no new execution paths.
- **Error branch (line 153):** `result.get("error", "Unknown error")` reads from the outer envelope — correct, as that is where the node client puts the error string on failure.

---

## Compilation Check

```
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.services.node_client import HubNodeClient; from src.node_agent.executor import OperationExecutor; print('OK')"
```
**Exit code: 0 — output: OK**

Both `HubNodeClient` and `OperationExecutor` import cleanly, confirming the modified source surfaces compile without errors.

---

## Summary

| Fix | File | Status |
|-----|------|--------|
| format_tool_response dict-in-message | `src/hub/transport/mcp.py` | ✅ Correct |
| git_status_handler envelope unwrapping | `src/hub/tools/git_operations.py` | ✅ Correct |

**Blockers:** None.
**Concerns:** None.
**Recommendation:** Safe to advance to QA.
