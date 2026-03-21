# QA Verification for FIX-015: Fix Task UUID handling and CLI entrypoint packaging

## Acceptance Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | TaskRepository handles both UUID and string task_ids without crashing | **PASS** | `_row_to_task` in `src/shared/repositories/tasks.py:215-221` uses try/except to parse UUID, falling back to string |
| 2 | CLI entrypoints work after pip install | **PASS** | `pyproject.toml:52` includes `scripts*` in package discovery; console scripts defined at lines 23-26 |
| 3 | Package discovery includes scripts/ or entrypoints reference src/ | **PASS** | `pyproject.toml:52` explicitly includes `scripts*` in the include list |

## Verification Details

### Criterion 1: TaskRepository UUID Handling

**Code Location:** `src/shared/repositories/tasks.py:215-221`

```python
# Handle both UUID and string task_ids
task_id_value = row["task_id"]
try:
    task_id = UUID(task_id_value)
except ValueError:
    # Not a valid UUID, use as string
    task_id = task_id_value
```

**Verification:** 
- The `_row_to_task` method now correctly handles both UUID and string task_ids
- All repository methods (`get`, `get_by_trace`, `list_all`, `list_by_outcome`, `list_by_tool`, `list_recent`) use this method
- The `TaskRecord.task_id` type in `src/shared/models.py:138` has been updated to `UUID | str`

### Criterion 2: CLI Entry Points

**Code Location:** `pyproject.toml:23-26` and `pyproject.toml:50-52`

```toml
[project.scripts]
gpttalker-validate = "scripts.validate:main"
gpttalker-test = "scripts.run_tests:main"
gpttalker-lint = "scripts.run_lint:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*", "scripts*"]
```

**Verification:**
- Console scripts are properly defined
- Package discovery now includes `scripts*` so scripts are bundled on pip install
- Entry points reference `scripts.validate:main`, etc., which will work with the updated package discovery

### Criterion 3: Package Discovery

**Code Location:** `pyproject.toml:50-52`

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["src*", "scripts*"]
```

**Verification:**
- The include list now explicitly includes `scripts*`
- This allows the scripts directory to be bundled when the package is installed

## Code Quality

- **Type annotations:** Updated to reflect `UUID | str` for task_id fields
- **Backward compatibility:** Existing UUID task IDs continue to work (try block succeeds)
- **Forward compatibility:** String task IDs (e.g., human-readable IDs like "task-001") now work

## Summary

All 3 acceptance criteria verified via code inspection. The implementation correctly fixes:
1. UUID/string handling in TaskRepository
2. CLI entry point packaging
3. Package discovery to include scripts directory

**QA Result: PASS**
