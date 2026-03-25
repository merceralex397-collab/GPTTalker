# EXEC-005 Implementation

## Summary
Applied three targeted fixes to align write_markdown and MCP transport response contracts with test expectations.

## Changes Applied

### 1. `src/hub/tools/markdown.py`

**Parameter renaming** — handler signature changed from `node/write_target/relative_path` to `node_id/repo_id/path`:
- `node: str` → `node_id: str`
- `write_target: str` → `repo_id: str`
- `relative_path: str` → `path: str`
- All internal references updated throughout the handler

**Policy lookup** — changed from `write_target_policy.get(write_target)` to `write_target_policy.list_write_targets_for_repo(repo_id)`:
```python
targets = await write_target_policy.list_write_targets_for_repo(repo_id)
if not targets:
    return {"success": False, "error": f"No write targets found for repo: {repo_id}"}
allowed_target = targets[0]
```

### 2. `src/hub/tools/__init__.py`

**Schema parameter names** updated to match test expectations:
- `"node"` → `"node_id"`
- `"write_target"` → `"repo_id"`
- `"relative_path"` → `"path"`
- Required list: `["node_id", "repo_id", "path", "content"]`

### 3. `src/hub/transport/mcp.py`

**format_tool_response nesting fix** — prevents double-wrapping when result already has a `data` key:
```python
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

This fixes the test where `result = {"data": "test result"}` was being wrapped as `{"success": True, "data": {"data": "test result"}}`, causing `response["result"]["data"] == "test result"` to fail.

## Verification

Syntax check: all three files pass `python -m py_compile`
Scoped tests: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py::TestWriteTools tests/hub/test_transport.py::test_format_tool_response_success -v --tb=short`
