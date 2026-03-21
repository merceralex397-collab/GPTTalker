# Plan Review: FIX-015 - Fix Task UUID handling and CLI entrypoint packaging

## Decision: APPROVED

## Summary

The plan correctly identifies both issues and proposes feasible fixes. The plan is complete and ready for implementation.

## Findings

### Issue 1: Task UUID Handling ✅

**Verification:**
- `TaskRepository.create()` accepts `task_id: UUID | str` (tasks.py:28)
- Task IDs are stored as strings (tasks.py:67: `task_id_str = str(task_id)`)
- `_row_to_task()` at line 216 unconditionally uses `UUID(row["task_id"])` - **confirmed bug**

**Observation:** The plan correctly identifies the fix approach (try/except with string fallback). However, the plan notes as a risk that `TaskRecord.task_id` may need updating. This is **confirmed required** - the model at `models.py:138` defines `task_id: UUID` (not `UUID | str`), so the implementer MUST also update this field type.

### Issue 2: CLI Entrypoint Packaging ✅

**Verification:**
- `pyproject.toml` lines 23-26 define `[project.scripts]`
- Line 52: `include = ["src*"]` - scripts directory not included
- **Confirmed root cause:** entrypoints will fail because scripts/ isn't packaged

**Plan correctly proposes:** Add `scripts*` to the include list.

## Acceptance Criteria Coverage

| Criterion | Status |
|-----------|--------|
| TaskRepository handles both UUID and string task_ids without crashing | ✅ Addressed (with model update needed) |
| CLI entrypoints work after pip install | ✅ Addressed |
| Package discovery includes scripts/ | ✅ Addressed |

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| TaskRecord.task_id type needs update | Low | Implementer must add `UUID | str` union to models.py |

## No Blockers

All required information is present. No missing decisions or validation gaps identified.
