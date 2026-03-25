# EXEC-005 Planning: Align write_markdown and MCP transport response contracts

## Ticket
- **ID**: EXEC-005
- **Title**: Align write_markdown and MCP transport response contracts with tests
- **Wave**: 9
- **Lane**: bugfix
- **Stage**: planning

## Root Cause Summary

Two contract mismatches cause 6 test failures:

1. **`write_markdown_handler()` parameter names**: Handler signature uses `node`, `write_target`, `relative_path` but tests call with `node_id`, `repo_id`, `path`. Plus, handler uses `write_target_policy.get(write_target)` but tests mock `list_write_targets_for_repo(repo_id)`.

2. **`format_tool_response()` nesting**: The handler returns `{"success": True, "data": {...}}` and passes the full dict to `format_tool_response`, which wraps it as `{"success": True, "data": {"success": True, ...}}`. The test passes `{"data": "test result"}` as result and expects `response["result"]["data"] == "test result"` (the string), not a nested dict.

## Issue 1: write_markdown_handler parameter mismatch

### Current handler signature (`src/hub/tools/markdown.py` lines 33–42):
```python
async def write_markdown_handler(
    node: str,
    write_target: str,
    relative_path: str,
    content: str,
    mode: str = "create_or_overwrite",
    ...
)
```

### Test calls use (`tests/hub/test_contracts.py`):
```python
write_markdown_handler(
    node_id="test-node-1",
    repo_id="test-repo-1",
    path="test.md",
    content="# Test content",
    ...
)
```

**Error**: `TypeError: unexpected keyword argument 'node_id'`

### Additional issue: `write_target_policy.get(write_target)` vs `list_write_targets_for_repo(repo_id)`
- Handler uses `write_target_policy.get(write_target)` — expects a write target ID
- Tests mock `list_write_targets_for_repo(repo_id)` — returns list of targets for a repo
- `get` method signature: takes a write target ID, returns a single target
- `list_write_targets_for_repo` method: takes a repo ID, returns a list of targets

The handler needs to:
1. Accept `repo_id` parameter
2. Call `list_write_targets_for_repo(repo_id)` to get available targets
3. Use the first target from the returned list

### Fix plan for Issue 1

**File: `src/hub/tools/markdown.py`**

1. Change handler signature parameters:
   - `node: str` → `node_id: str`
   - `write_target: str` → `repo_id: str`
   - `relative_path: str` → `path: str`

2. Change write target lookup:
   ```python
   # OLD (line 98):
   allowed_target = await write_target_policy.get(write_target)
   
   # NEW:
   allowed_targets = await write_target_policy.list_write_targets_for_repo(repo_id)
   if not allowed_targets:
       return {"success": False, "error": f"No write targets found for repo: {repo_id}"}
   allowed_target = allowed_targets[0]
   ```

3. Update internal references:
   - Line 152: `PathNormalizer.normalize(full_path, allowed_target.path)` — `allowed_target` is still a write target object with `.path`, so this is fine

**File: `src/hub/tools/__init__.py`** (MCP tool registration)

Update the `write_markdown` tool registration to use the new parameter names:

```python
"properties": {
    "node_id": {"type": "string", "description": "Node identifier (required)"},
    "repo_id": {"type": "string", "description": "Repository identifier (required)"},
    "path": {"type": "string", "description": "File path relative to write target root (required)"},
    "content": {"type": "string", "description": "Markdown content to write (required)"},
    "mode": {...},
},
"required": ["node_id", "repo_id", "path", "content"],
```

Note: The MCP schema is what ChatGPT sees. The handler is what the router calls. Both need to agree. Changing the handler to `node_id/repo_id/path` means the router passes `node_id/repo_id/path` to the handler, so the MCP schema must also declare `node_id/repo_id/path`.

## Issue 2: format_tool_response nesting mismatch

### Current behavior:
```python
# Handler returns:
{"success": True, "write_target": ..., "node": ..., ...}

# format_tool_response does:
response["result"] = {
    "success": True,  # from handler result
    "data": handler_result,  # entire handler dict
    "duration_ms": duration_ms,
}

# Final: response["result"]["data"] = {"success": True, "write_target": ..., ...}
```

### Test expectation:
```python
result = {"data": "test result"}  # test passes this as result
# Expects: response["result"]["data"] == "test result" (the string)
# But current code gives: response["result"]["data"] = {"data": "test result"}
```

The test is checking the MCP response shape. The MCP result should be the tool's return value directly. When the handler returns a dict with a `data` key, the MCP response's `data` field should be the value of that `data` key, not the whole handler dict.

### Fix plan for Issue 2

**File: `src/hub/transport/mcp.py`** — `format_tool_response` function

```python
# OLD (lines 136-141):
response["result"] = {
    "success": True,
    "data": result,
    "duration_ms": duration_ms,
}

# NEW:
if isinstance(result, dict) and "data" in result:
    # Handler returned a structured dict; extract the data field for MCP result
    response["result"] = result
    response["result"]["duration_ms"] = duration_ms
else:
    # Simple result (backward compatibility for tests)
    response["result"] = {
        "success": True,
        "data": result,
        "duration_ms": duration_ms,
    }
```

This handles both cases:
- Handler returns `{"success": True, "data": {...}}` → MCP result is the full handler dict (preserving existing behavior for real tools)
- Test passes `{"data": "test result"}` → MCP result data is `"test result"` (满足测试期望)

Wait — for the test case `{"data": "test result"}`:
- `isinstance(result, dict) and "data" in result` → True
- `response["result"] = result` → `response["result"] = {"data": "test result"}`
- `response["result"]["data"]` = `"test result"` ✓

And for write_markdown handler returning `{"success": True, "data": {...}}`:
- `isinstance(result, dict) and "data" in result` → True
- `response["result"] = result` → `response["result"] = {"success": True, "data": {...}}`
- `response["result"]["success"]` = `True` ✓
- `response["result"]["data"]` = `{...}` (the handler's data field) ✓

This looks correct.

## Files to Modify

1. **`src/hub/tools/markdown.py`** — Change handler signature from `node/write_target/relative_path` to `node_id/repo_id/path`, change write target lookup to use `list_write_targets_for_repo`

2. **`src/hub/tools/__init__.py`** — Update write_markdown MCP tool registration parameter names to match handler

3. **`src/hub/transport/mcp.py`** — Fix `format_tool_response` to extract `result["data"]` when result is a dict with a `data` key

## Validation Plan

After changes:
1. `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.tools.markdown import write_markdown_handler; print('import ok')"` — verify no import errors
2. `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.transport.mcp import format_tool_response; print(format_tool_response({'data': 'test'}))"` — verify nesting fix
3. `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -k write_markdown -q --tb=short` — 5 failures should become 0
4. `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_transport.py -k format_tool_response -q --tb=short` — 1 failure should become 0

## Non-regression Plan

The fix should not change:
- The handler's success/error response structure (still returns `{"success": True/False, ...}`)
- The `duration_ms`, `trace_id`, `message_id` handling
- Any other tool's behavior

## Interaction with FIX-009

FIX-009 changed the handler to use `node/write_target/relative_path` from the MCP schema perspective. The tests still use `node_id/repo_id/path`. This EXEC-005 fix:
- Updates the handler to accept `node_id/repo_id/path` (matching tests)
- Updates the MCP registration to use `node_id/repo_id/path` (still matching tests)
- This is effectively reverting the parameter name part of FIX-009's handler signature change, while preserving FIX-009's `mode` parameter and other behavioral fixes
