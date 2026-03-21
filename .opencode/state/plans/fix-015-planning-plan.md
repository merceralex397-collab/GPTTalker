# Implementation Plan: FIX-015 - Fix Task UUID handling and CLI entrypoint packaging

## Scope
Fix two unrelated issues in the GPTTalker project:
1. TaskRepository crashes when retrieving tasks with string IDs instead of UUIDs
2. CLI entrypoints don't work after pip install because scripts/ directory isn't included in package

## Files or Systems Affected
- `src/shared/repositories/tasks.py` - TaskRepository._row_to_task method
- `pyproject.toml` - Package discovery and scripts configuration

## Issue 1: Task UUID Handling

### Current State
- `TaskRepository.create()` accepts `task_id: UUID | str` (line 28)
- Task IDs are stored as strings in SQLite (line 67: `task_id_str`)
- `_row_to_task()` at line 216 always parses as `UUID(row["task_id"])`, causing `ValueError` on string IDs

### Root Cause
The `_row_to_task` method assumes all task_ids are valid UUIDs, but the system may store string-based task IDs (e.g., human-readable IDs like "task-001").

### Fix Approach
Modify `_row_to_task` to handle both UUID and plain string task_ids:
1. Attempt to parse as UUID first
2. If that fails, treat as a plain string and construct TaskRecord with string task_id

### Implementation Steps
1. **Modify `_row_to_task` in `src/shared/repositories/tasks.py`**:
   - Wrap `UUID(row["task_id"])` in try/except
   - On `ValueError`, use the string directly
   - Ensure TaskRecord accepts both UUID and str for task_id field

2. **Verify TaskRecord model accepts string task_id**:
   - Check `src/shared/models.py` for TaskRecord definition
   - If task_id is typed as UUID only, update to `UUID | str`

### Validation
- Write test that creates task with string ID, retrieves it, and verifies no crash
- Write test that creates task with UUID, retrieves it, and verifies correct parsing

## Issue 2: CLI Entrypoint Packaging

### Current State
- `pyproject.toml` line 23-26 defines `[project.scripts]`:
  ```
  gpttalker-validate = "scripts.validate:main"
  gpttalker-test = "scripts.run_tests:main"
  gpttalker-lint = "scripts.run_lint:main"
  ```
- `pyproject.toml` line 50-51 defines package discovery:
  ```
  [tool.setuptools.packages.find]
  where = ["."]
  include = ["src*"]
  ```

### Root Cause
The `scripts/` directory is not included in the package (only `src*` is), so when the package is installed via pip, the scripts aren't available and the entrypoints fail.

### Fix Approach
Update package discovery to include the scripts directory. Two options:
1. **Option A (Recommended)**: Add `scripts*` to the include list
2. **Option B**: Move scripts into `src/` (more invasive, not recommended)

### Implementation Steps
1. **Modify `pyproject.toml`**:
   - Change line 51 from `include = ["src*"]` to `include = ["src*", "scripts*"]`

2. **Verify scripts are importable after install**:
   - The scripts currently use `sys.path.insert(0, ...)` to add src to path (line 6-7 in `scripts/__init__.py`)
   - After pip install, this path adjustment should still work since src will be in the package

### Validation
- Run `pip install -e .` in a test environment
- Verify `gpttalker-validate`, `gpttalker-test`, `gpttalker-lint` commands work

## Implementation Order
1. Fix TaskRepository._row_to_task (UUID handling)
2. Fix pyproject.toml package discovery
3. Run validation tests

## Validation Plan

### UUID Handling
1. Run existing tests: `pytest tests/ -v`
2. Manually verify with test script that creates string ID task and retrieves it

### CLI Packaging
1. Run: `pip install -e .` 
2. Run: `gpttalker-lint --help` (should not error)
3. Run: `gpttalker-validate` (should execute validation)

## Risks and Assumptions
- **Risk**: TaskRecord model may need update if task_id is typed as UUID-only
- **Assumption**: Moving scripts* into include won't conflict with src* patterns
- **Assumption**: The sys.path manipulation in scripts/__init__.py will continue to work post-install

## Blockers
- None identified - both issues are well-contained and isolated

## Acceptance Criteria Tracking

| Criterion | Status |
|-----------|--------|
| TaskRepository handles both UUID and string task_ids without crashing | Not started |
| CLI entrypoints work after pip install | Not started |
| Package discovery includes scripts/ | Not started |
