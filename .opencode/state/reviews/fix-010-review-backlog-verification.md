# Backlog Verification — FIX-010

## Ticket
- **ID:** FIX-010
- **Title:** Implement missing observability tools and audit persistence
- **Stage:** closeout
- **Status:** done
- **Verification state:** PASS

## Verification Summary
Three gaps fixed:
1. `list_known_issues` — implemented and registered, queries IssueRepository and Qdrant
2. `list_task_history` — implemented and registered, queries SQLite tasks table
3. Task call persistence — `handle_tool_call` now persists trace_id, tool_name, caller, outcome, duration_ms to tasks table

## Evidence
1. **list_known_issues:** Handler queries `IssueRepository.list()` with optional repo_id filter
2. **list_task_history:** Handler queries `TaskRepository.list()` with pagination support
3. **Audit persistence:** Tool calls are recorded in the tasks table with full trace metadata

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| list_known_issues tool is registered and returns issues | PASS |
| list_task_history tool is registered and returns task audit log | PASS |
| Every tool call persists trace_id, tool_name, caller, outcome, duration_ms | PASS |

## Notes
- This ticket completed the observability surface defined in the canonical brief
- Observability tools (OBS-001, OBS-002) provided the schema; this ticket filled the implementation gaps
- No follow-up ticket needed
