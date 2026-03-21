# Implementation of FIX-010: Implement missing observability tools and audit persistence

## Summary

Implemented FIX-010: "Implement missing observability tools and audit persistence". The implementation adds:

1. `list_known_issues` tool - Lists issues from SQLite with optional filtering
2. `list_task_history` tool - Lists task history from SQLite with optional filtering  
3. Task persistence in `handle_tool_call` - Every tool call now persists audit data

## Changes Made

### 1. src/hub/tools/observability.py

Added two new handlers:

**list_known_issues_handler**:
- Lists issues from SQLite using IssueRepository methods
- Parameters: `repo_id`, `status`, `limit`
- Returns structured list of issues with metadata

**list_task_history_handler**:
- Lists task history using TaskRepository methods
- Parameters: `outcome`, `tool_name`, `hours`, `limit`
- Returns structured list of task records

### 2. src/hub/tools/__init__.py

Registered both new tools:
- `list_known_issues` with NO_POLICY_REQUIREMENT
- `list_task_history` with NO_POLICY_REQUIREMENT

### 3. src/hub/routes.py

Modified `call_tool` endpoint:
- Added `req: Request` parameter to access app state
- Extracts `db_manager` from `req.app.state.db_manager` if available
- Passes `db_manager` to `handle_tool_call()`

### 4. src/hub/mcp.py

Added task persistence logic:
- Added imports for `uuid4` and `TaskOutcome`
- Added `db_manager` parameter to `handle_tool_call` method
- Added auto-generation of trace_id if not provided
- Added task persistence after each tool execution with:
  - `task_id` (UUID)
  - `tool_name`
  - `caller` (set to "mcp")
  - `outcome` (SUCCESS or ERROR)
  - `duration_ms`
  - `trace_id`
  - `error` (if failed)
- Wrapped in try/except to not fail tool calls if persistence fails

## Acceptance Criteria

- ✅ list_known_issues tool is registered and returns issues from SQLite
- ✅ list_task_history tool is registered and returns task audit log from SQLite
- ✅ Every tool call persists trace_id, tool_name, caller, outcome, duration_ms to tasks table