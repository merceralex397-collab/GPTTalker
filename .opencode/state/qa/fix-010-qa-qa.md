# QA Verification: FIX-010

## Summary
QA verification for FIX-010: Implement missing observability tools and audit persistence.

## Acceptance Criteria Results

| Criterion | Result |
|-----------|--------|
| 1. list_known_issues tool registered and returns issues | ✅ PASS |
| 2. list_task_history tool registered and returns tasks | ✅ PASS |
| 3. Tool calls persist to tasks table | ✅ PASS |

## Detailed Verification

### Criterion 1: list_known_issues tool is registered and returns issues from SQLite/Qdrant

**Evidence:**
- `list_known_issues_handler` in observability.py uses IssueRepository methods
- Tool registered in __init__.py with NO_POLICY_REQUIREMENT

**Result: PASS**

### Criterion 2: list_task_history tool is registered and returns task audit log from SQLite

**Evidence:**
- `list_task_history_handler` in observability.py uses TaskRepository methods
- Tool registered in __init__.py with NO_POLICY_REQUIREMENT

**Result: PASS**

### Criterion 3: Every tool call persists to tasks table

**Evidence:**
- mcp.py lines 113-140: Task persistence logic in handle_tool_call
- routes.py lines 73-84: db_manager extracted from app.state and passed

**Result: PASS**

## Overall: PASS

All acceptance criteria are satisfied.