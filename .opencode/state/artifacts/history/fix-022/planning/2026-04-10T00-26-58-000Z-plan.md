# Plan for FIX-022: Fix HubNodeClient.read_file HTTP Method and Endpoint Mismatch

## Problem Statement

`HubNodeClient.read_file` in `src/hub/services/node_client.py` uses:
- HTTP method: `GET`
- Endpoint: `/files/read?path={path}`
- No offset/limit parameters

The node agent only exposes:
- HTTP method: `POST`
- Endpoint: `/operations/read-file`
- Request body: `{"path": path, "offset": offset, "limit": limit}`

This contract mismatch causes the hub's `read_file` tool to always fail.

## Current Code Analysis

### HubNodeClient.read_file (lines 181-203)
```python
async def read_file(
    self,
    node: NodeInfo,
    path: str,
) -> dict[str, Any]:
    response = await self.get(node, f"/files/read?path={path}", timeout=30.0)
    if response.status_code == 200:
        return response.json()
    return {
        "success": False,
        "error": f"Failed to read file: HTTP {response.status_code}",
    }
```

### Node Agent ReadFileRequest (operations.py lines 32-36)
```python
class ReadFileRequest(OperationRequest):
    """Request to read a file."""
    offset: int = 0
    limit: int | None = None
```

### Node Agent read_file endpoint (operations.py lines 136-191)
- Route: `POST /operations/read-file`
- Returns: `OperationResponse(success, message, data)`
- File content is in `response.json()["data"]`

## Required Changes

### 1. Update HubNodeClient.read_file signature
Add `offset` and `limit` parameters to match the node agent's `ReadFileRequest`:

```python
async def read_file(
    self,
    node: NodeInfo,
    path: str,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
```

### 2. Change HTTP method from GET to POST and update endpoint path
Replace:
```python
response = await self.get(node, f"/files/read?path={path}", timeout=30.0)
```

With:
```python
response = await self.post(
    node,
    "/operations/read-file",
    json={"path": path, "offset": offset, "limit": limit},
    timeout=30.0,
)
```

### 3. Update response parsing
The node agent returns `OperationResponse` with the file content inside `data`. Change response parsing from:
```python
if response.status_code == 200:
    return response.json()
```

To:
```python
if response.status_code == 200:
    data = response.json()
    if data.get("success"):
        return data.get("data", {})
    return {"success": False, "error": data.get("message", "Unknown error")}
```

This matches the pattern used by other methods in the same file (e.g., `search`, `git_status`, `list_directory`).

## Files to Modify

| File | Change |
|------|--------|
| `src/hub/services/node_client.py` | Update `read_file` method: change GET→POST, endpoint `/files/read`→`/operations/read-file`, add offset/limit params, update response parsing |

## No Changes Needed

- `src/node_agent/routes/operations.py` - already correct, no changes needed
- No new imports required - `HubNodeClient` already has `post()` method

## Implementation Steps

1. **Update method signature**: Add `offset: int = 0` and `limit: int | None = None` parameters to `read_file()`
2. **Change HTTP call**: Replace `self.get(node, f"/files/read?path={path}", ...)` with `self.post(node, "/operations/read-file", json={...}, ...)`
3. **Update response parsing**: Extract file content from `response.json()["data"]` following the `OperationResponse` pattern
4. **Preserve error handling**: Keep the existing error return structure

## Validation Plan

### Acceptance Criteria Verification

1. **HTTP method and endpoint**: Code inspection confirms `POST /operations/read-file` with JSON body
2. **Offset/limit parameters**: Code inspection confirms parameters passed through to node agent
3. **Hub import test**: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.services.node_client import HubNodeClient; print("OK")'`
4. **Node agent import test**: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.node_agent.routes.operations import router; print("OK")'`

### Code Quality Checks
- Syntax validation via Python compile
- Response parsing follows existing pattern in `node_client.py` (same as `search`, `git_status`, `list_directory`)
- Error handling preserves existing behavior

## Alternative Considered

None - the current implementation is clearly incorrect. The node agent only exposes `POST /operations/read-file` and the hub is using a non-existent `GET /files/read` endpoint. No architectural alternatives needed for this straightforward bug fix.
