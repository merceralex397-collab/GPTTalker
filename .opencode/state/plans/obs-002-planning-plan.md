# Planning: OBS-002

## Ticket
- **ID**: OBS-002
- **Title**: Task detail, doc history, and issue timeline tools
- **Wave**: 5
- **Lane**: observability

## Summary
Expose observability-facing tools for task details, generated document history, and issue timelines.

## Acceptance Criteria
1. Observability tool outputs are structured
2. Task-detail lookups cite persisted records
3. Issue timeline reads from the canonical history store

## Dependencies
- OBS-001 (Task history, generated-doc log, and audit schema)
- CTX-003 (get_project_context and known-issue records)

## Analysis

### What's Already Done (from OBS-001)
- `TaskRecord` model and `tasks` table
- `GeneratedDocRecord` model and `generated_docs` table
- `AuditRecord` model and `audit_log` table
- Repositories: `TaskRepository`, `GeneratedDocsRepository`, `AuditLogRepository`

### What's Needed
Three new MCP tools:

1. **get_task_details** - Lookup specific task by ID or trace_id
   - Input: task_id or trace_id
   - Returns: Full TaskRecord details
   - Uses: TaskRepository

2. **list_generated_docs** - List generated document history
   - Input: Optional filters (owner_type, owner_id, repo_id, limit)
   - Returns: List of GeneratedDocRecord with pagination
   - Uses: GeneratedDocsRepository

3. **get_issue_timeline** - Get issue timeline/history
   - Input: repo_id, issue_id (optional), limit
   - Returns: Timeline of issue events from IssueRepository
   - Uses: IssueRepository

## Implementation Plan

### New Files
1. `src/hub/tools/observability.py` - MCP tool handlers

### Modifications
1. `src/hub/tools/__init__.py` - Register new tools
2. `src/hub/dependencies.py` - Add repositories if not already

### Tools Registration
- `get_task_details`: NO_POLICY_REQUIREMENT (observability read)
- `list_generated_docs`: NO_POLICY_REQUIREMENT (observability read)
- `get_issue_timeline`: READ_REPO_REQUIREMENT (needs repo access)

## Integration Points
- TaskRepository from OBS-001
- GeneratedDocsRepository from OBS-001
- IssueRepository from SETUP-003/CTX-003

## Validation
- Unit tests for each tool handler
- Integration tests verifying repository integration
