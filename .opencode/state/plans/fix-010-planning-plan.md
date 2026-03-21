# Implementation Plan for FIX-010: Implement missing observability tools and audit persistence

## 1. Scope

This ticket addresses three observability gaps:
1. **list_known_issues** tool is not implemented or registered
2. **list_task_history** tool is not implemented or registered  
3. **Task persistence** is missing from `handle_tool_call` - no audit data is written to SQLite

## 2. Files/Systems Affected

### Existing Files to Modify
| File | Changes Needed |
|------|----------------|
| `src/hub/tools/observability.py` | Add `list_known_issues_handler` and `list_task_history_handler` implementations |
| `src/hub/tools/__init__.py` | Add tool registrations for both new handlers in `register_observability_tools()` |
| `src/hub/routes.py` | Add `request: Request` parameter to `call_tool` route, pass db_manager to handler |
| `src/hub/mcp.py` | Add imports for `uuid` and `TaskOutcome`, modify `handle_tool_call` to accept optional `db_manager` parameter, add task persistence logic |

### No New Files Required
All functionality can be implemented in existing files using existing repository methods.

## 3. Implementation Steps

### Step 1: Add `list_known_issues_handler` to observability.py

Add a new handler function that:
- Uses existing `IssueRepository.list_all()`, `list_by_repo()`, or `list_by_status()` methods
- Accepts parameters: `repo_id`, `status`, `limit`
- Returns structured list of issues with metadata
- Uses existing DI pattern: `issue_repo: "IssueRepository | None"` parameter

```python
async def list_known_issues_handler(
    repo_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    issue_repo: "IssueRepository | None" = None,
) -> dict[str, Any]:
    """List known issues with optional filtering."""
    # Implementation uses issue_repo.list_all(), list_by_repo(), or list_by_status()
```

### Step 2: Add `list_task_history_handler` to observability.py

Add a new handler function that:
- Uses existing `TaskRepository.list_all()`, `list_by_outcome()`, `list_by_tool()`, or `list_recent()` methods
- Accepts parameters: `outcome`, `tool_name`, `hours`, `limit`
- Returns structured list of task records with metadata
- Uses existing DI pattern: `task_repo: "TaskRepository | None"` parameter

```python
async def list_task_history_handler(
    outcome: str | None = None,
    tool_name: str | None = None,
    hours: int | None = None,
    limit: int = 100,
    task_repo: "TaskRepository | None" = None,
) -> dict[str, Any]:
    """List task history with optional filtering."""
    # Implementation uses task_repo.list_all(), list_by_outcome(), list_by_tool(), or list_recent()
```

### Step 3: Register both tools in tools/__init__.py

Add to `register_observability_tools()` function:
- `list_known_issues` tool with `NO_POLICY_REQUIREMENT`
- `list_task_history` tool with `NO_POLICY_REQUIREMENT`

### Step 4: Add task persistence to handle_tool_call in mcp.py

**Architectural approach**: Pass `db_manager` to `handle_tool_call` from the route.

**Changes needed**:

1. **mcp.py**: Add imports at top of file:
```python
from uuid import uuid4
from src.shared.models import TaskOutcome
```

2. **routes.py**: Modify `call_tool` to accept `request: Request` and pass db_manager:
```python
@router.post("/mcp/v1/tools/call")
async def call_tool(request: MCPToolCallRequest, req: Request):
    # ... existing code ...
    result = await mcp_handler.handle_tool_call(
        tool_name=request.tool_name,
        parameters=request.parameters,
        trace_id=request.trace_id,
        db_manager=req.app.state.db_manager if hasattr(req.app.state, 'db_manager') else None,
    )
```

3. **mcp.py**: Modify `handle_tool_call` signature and add persistence:
```python
async def handle_tool_call(
    self,
    tool_name: str,
    parameters: dict,
    trace_id: str | None = None,
    db_manager: "DatabaseManager | None" = None,  # Add this parameter
) -> dict[str, Any]:
    # ... existing code up to route_tool() ...

    # After tool execution, persist task data
    if db_manager is not None:
        task_repo = TaskRepository(db_manager)
        # Check success from nested result structure
        is_success = result.get("result", {}).get("success", False)
        outcome = TaskOutcome.SUCCESS if is_success else TaskOutcome.ERROR
        error_msg = result.get("error", {}).get("message") if not is_success else None
        await task_repo.create(
            task_id=uuid4(),
            tool_name=tool_name,
            caller="mcp",  # Default caller for MCP calls
            outcome=outcome,
            duration_ms=duration_ms,
            trace_id=trace_id,
            error=error_msg,
        )
```

## 4. Validation Plan

### Acceptance Criteria Verification

| Criterion | Verification Method |
|-----------|---------------------|
| `list_known_issues` tool is registered | Check `register_all_tools()` includes the new registration |
| `list_known_issues` returns issues from SQLite | Verify IssueRepository methods are called |
| `list_task_history` tool is registered | Check registration in `register_observability_tools()` |
| `list_task_history` returns task audit log | Verify TaskRepository methods are called |
| Every tool call persists to tasks table | Verify TaskRepository.create() is called in handle_tool_call |

### Test Commands

```bash
# Verify tool registration
python3 -c "from src.hub.tools import register_all_tools; from src.hub.tool_router import ToolRegistry; r = ToolRegistry(); register_all_tools(r); print([t.name for t in r.list_tools()])"

# Verify Python syntax
python3 -m py_compile src/hub/tools/observability.py
python3 -m py_compile src/hub/mcp.py
python3 -m py_compile src/hub/routes.py

# Verify imports work
python3 -c "from src.hub.tools.observability import list_known_issues_handler, list_task_history_handler"
```

## 5. Blockers

No blocking decisions required. All required components exist.

## 6. Acceptance

- [ ] list_known_issues tool is registered and returns issues from SQLite/Qdrant
- [ ] list_task_history tool is registered and returns task audit log from SQLite
- [ ] Every tool call persists trace_id, tool_name, caller, outcome, duration_ms to tasks table