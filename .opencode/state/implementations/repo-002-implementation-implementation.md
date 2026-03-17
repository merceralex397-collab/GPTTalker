# REPO-002 Implementation Summary: inspect_repo_tree and read_repo_file Tools

## Overview

This ticket implements two MCP tools for repository inspection:
- `inspect_repo_tree`: Lists directory contents within approved repos
- `read_repo_file`: Reads file contents with offset/limit support

## Implementation Details

### New Files Created

1. **`src/hub/tools/inspection.py`** (312 lines)
   - `inspect_repo_tree_handler`: Hub-side handler for directory listing
   - `read_repo_file_handler`: Hub-side handler for file reading
   - Both handlers use READ_REPO_REQUIREMENT policy
   - Full path validation using PathNormalizer
   - Integration with HubNodeClient for node communication

### Modified Files

2. **`src/hub/services/node_client.py`**
   - Added `list_directory()` method - calls node-agent `/operations/list-dir`
   - Added `read_file()` method - calls node-agent `/operations/read-file`
   - Both methods accept path, offset, limit parameters

3. **`src/hub/tools/__init__.py`**
   - Added `register_inspection_tools()` function
   - Registered both tools with ToolDefinition
   - Added `register_all_tools()` to register all tools
   - Updated `src/hub/main.py` to call `register_all_tools()`

4. **`src/hub/tool_routing/policy_router.py`**
   - Added `node_client` parameter to PolicyAwareToolRouter
   - Updated `_execute_handler()` to pass node_client to handlers

5. **`src/hub/dependencies.py`**
   - Updated `get_policy_aware_router()` to inject node_client

6. **`src/node_agent/executor.py`**
   - Implemented `list_directory()` with metadata (name, path, is_dir, size, modified)
   - Implemented `read_file()` with offset/limit support
   - Returns structured data including truncation info

7. **`src/node_agent/routes/operations.py`**
   - Implemented `/operations/list-dir` endpoint
   - Implemented `/operations/read-file` endpoint
   - Proper error handling with structured responses

## Architecture

```
ChatGPT → Hub (policy validation) → Node Agent (bounded file ops)
         ├── validate node_id (NodePolicy)
         ├── validate repo_id (RepoPolicy)
         ├── normalize & validate path (PathNormalizer)
         └── proxy to node-agent via HubNodeClient
```

## Policy Integration

Both tools use `READ_REPO_REQUIREMENT` which requires:
- Valid node access
- Valid repo access
- Path normalization and traversal prevention

## Validation

- Path traversal attempts are rejected with explicit error messages
- Unknown nodes and repos return appropriate errors
- Responses are MCP-structured with success/error format

## Acceptance Criteria Met

| Criterion | Status |
|-----------|--------|
| Repo tree inspection scoped to approved repos | ✅ |
| File reads reject traversal | ✅ |
| Responses structured for MCP | ✅ |

## Files Created/Modified Summary

| File | Action |
|------|--------|
| `src/hub/tools/inspection.py` | Created |
| `src/hub/services/node_client.py` | Modified |
| `src/hub/tools/__init__.py` | Modified |
| `src/hub/main.py` | Modified |
| `src/hub/tool_routing/policy_router.py` | Modified |
| `src/hub/dependencies.py` | Modified |
| `src/node_agent/executor.py` | Modified |
| `src/node_agent/routes/operations.py` | Modified |
