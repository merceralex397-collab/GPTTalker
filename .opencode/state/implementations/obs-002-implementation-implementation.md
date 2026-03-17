# Implementation: OBS-002

## Summary
Created observability tools for task details, generated document history, and issue timelines.

## Changes Made

### New Files
1. **src/hub/tools/observability.py** - Three new MCP tool handlers:
   - `get_task_details_handler` - Get task details by task_id or trace_id
   - `list_generated_docs_handler` - List generated document history with filtering
   - `get_issue_timeline_handler` - Get issue timeline/history

### Modified Files
1. **src/hub/dependencies.py**:
   - Added TaskRepository DI provider
   - Updated get_policy_router to inject task_repo and doc_repo

2. **src/hub/tool_routing/policy_router.py**:
   - Added TaskRepository and GeneratedDocsRepository to type hints
   - Added task_repo and doc_repo parameters to PolicyAwareToolRouter
   - Added handler injection for task_repo and doc_repo

3. **src/hub/tools/__init__.py**:
   - Added register_observability_tools() function
   - Registered all three observability tools with NO_POLICY_REQUIREMENT
   - Added call to register_observability_tools in register_all_tools()

## Acceptance Criteria
- Observability tool outputs are structured ✓
- Task-detail lookups cite persisted records ✓
- Issue timeline reads from the canonical history store ✓
