# Code Review for FIX-022: HubNodeClient.read_file HTTP Method and Endpoint Mismatch

## Verdict: NEEDS_FIXES

## Summary

The HTTP method and endpoint change is correct (GET → POST, `/files/read` → `/operations/read-file`), and the parameter mapping to `ReadFileRequest` is accurate. However, the response parsing does not follow the established `OperationResponse` pattern used by all other methods in this class.

## Findings

### 1. Response Parsing Inconsistency (Medium Severity)

**Location:** `src/hub/services/node_client.py`, lines 206-212

**Current implementation:**
```python
if response.status_code == 200:
    return response.json()

return {
    "success": False,
    "error": f"Failed to read file: HTTP {response.status_code}",
}
```

**Established pattern used by all other methods** (`search()`, `git_status()`, `list_directory()`):
```python
if response.status_code == 200:
    data = response.json()
    if data.get("success"):
        return data.get("data", {})
    return {"success": False, "error": data.get("message", "Unknown error")}

return {"success": False, "error": f"... HTTP {response.status_code}"}
```

**Issue:** The `read_file()` implementation returns `response.json()` directly without:
1. Checking the `success` field from `OperationResponse`
2. Extracting the `data` field containing the actual file content result

This means callers receive the raw `OperationResponse` structure (with `success`, `message`, `data` fields) instead of the unwrapped `data` content that all other methods return.

### 2. Correctly Implemented Items

| Item | Status |
|------|--------|
| HTTP method changed from GET to POST | ✅ Correct |
| Endpoint changed to `/operations/read-file` | ✅ Correct |
| JSON body with `path`, `offset`, `limit` | ✅ Correct |
| `ReadFileRequest` parameter mapping | ✅ Correct (`offset: int = 0`, `limit: int \| None = None`) |
| Timeout of 30.0s | ✅ Correct |
| Uses `self.post()` like other methods | ✅ Correct |

### 3. Compile/Import Verification Blocked

**Blocker:** The bash tool is denied, preventing execution of:
- `python3 -m py_compile src/hub/services/node_client.py`
- `python3 -m py_compile src/node_agent/routes/operations.py`  
- Import verification commands

The implementation artifact for FIX-022 claims these were verified in prior tickets (FIX-020, FIX-021), and syntax appears correct via code inspection. However, per workflow rules, I cannot approve on prose alone when the original check is re-runnable but blocked.

## Acceptance Criteria Status

| Criterion | Status |
|-----------|--------|
| HubNodeClient.read_file uses POST /operations/read-file with JSON body | ✅ VERIFIED |
| offset and limit parameters passed correctly | ✅ VERIFIED |
| Hub import succeeds | 🔲 BLOCKED (bash denied) |
| Node agent import succeeds | 🔲 BLOCKED (bash denied) |

## Required Fix

Update `read_file()` response parsing to match the established pattern:

```python
async def read_file(
    self,
    node: NodeInfo,
    path: str,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
    response = await self.post(
        node,
        "/operations/read-file",
        json={"path": path, "offset": offset, "limit": limit},
        timeout=30.0,
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data.get("data", {})
        return {"success": False, "error": data.get("message", "Unknown error")}

    return {
        "success": False,
        "error": f"Failed to read file: HTTP {response.status_code}",
    }
```

## Regression Risk

- **Low**: The change only affects `read_file()`. The HTTP method and endpoint change is exactly what was needed to fix the original bug.
- **Medium**: If a caller depends on the current raw `OperationResponse` return value (instead of the `data` content), this would be a breaking change. However, the canonical contract for all other methods returns the unwrapped `data` field.

## Recommendation

Request a fix to align response parsing with the established pattern, then re-run import verification commands. Do not approve until runtime validation commands execute successfully.
