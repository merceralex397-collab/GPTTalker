# Plan: EXEC-003 — Fix node-agent executor absolute-path validation within allowed roots

## Problem Statement

The diagnosis pack `diagnosis/20260325-071314/` reproduced 21 test failures in `tests/node_agent/test_executor.py` because `OperationExecutor._validate_path()` (src/node_agent/executor.py, lines 46-50) unconditionally rejects all absolute paths:

```python
# Step 1: Reject absolute paths
if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
    raise PermissionError(f"Absolute paths are not allowed: {path}")
```

This is too strict. Absolute paths that resolve **inside** the configured `allowed_paths` should be accepted — the security boundary is the `allowed_paths` root, not the relative-vs-absolute distinction.

The tests pass absolute paths to temp directories that are configured as `allowed_paths`:
```python
executor = OperationExecutor(allowed_paths=[tmpdir])
entries = await executor.list_directory(tmpdir)  # absolute path rejected
```

## Root Cause

`_validate_path()` conflates two distinct concerns:
1. **Absolute paths are suspicious** — a caller passing `/etc/passwd` instead of a relative `secrets/passwd` is unusual
2. **Out-of-bound paths are forbidden** — the actual security boundary is whether the resolved path stays inside `allowed_paths`

The current code rejects both in-bound and out-of-bound absolute paths. It should only reject out-of-bound absolute paths.

## Files Affected

| File | Change |
|---|---|
| `src/node_agent/executor.py` | Modify `_validate_path()` to allow absolute paths that resolve inside `allowed_paths`; only reject absolute paths that resolve outside roots |

## Trust Boundary

The fix preserves the security boundary: paths outside `allowed_paths` are still rejected. The fix only allows **in-root absolute paths** that were previously incorrectly rejected.

The `_validate_path` method's docstring currently says "must be relative, not absolute" — this will be updated to reflect the corrected behavior.

## Implementation Steps

### Step 1 — Modify `_validate_path()` in `src/node_agent/executor.py`

Change the method to:
1. Accept absolute paths (don't reject at step 1 unconditionally)
2. Resolve the absolute path to a real path
3. Check whether the resolved path is inside `allowed_paths`
4. Reject if outside `allowed_paths`

New logic:
```python
def _validate_path(self, path: str) -> Path:
    """Validate that a path is within allowed boundaries.

    Args:
        path: Path to validate (relative or absolute)

    Returns:
        Resolved absolute path

    Raises:
        PermissionError: If path is absolute or contains traversal
        PermissionError: If path is not within allowed boundaries
    """
    # Step 1: If absolute, resolve it; if relative, resolve against current dir
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        # Absolute path — resolve to real path
        resolved = Path(path).resolve()
    else:
        # Relative path — resolve from current working directory
        resolved = Path.cwd() / path

    # Step 2: Check for path traversal (.. components)
    path_parts = resolved.parts
    if ".." in path_parts:
        raise PermissionError(f"Path traversal is not allowed: {path}")

    # Step 3: Check if resolved path is within any allowed root
    for allowed in self.allowed_paths:
        allowed_resolved = Path(allowed).resolve()
        try:
            resolved.relative_to(allowed_resolved)
            return resolved  # Inside this allowed root
        except ValueError:
            continue  # Not inside this root, try next

    # Not inside any allowed root
    raise PermissionError(f"Path is outside allowed directories: {path}")
```

### Step 2 — Update docstring

Update the `_validate_path` docstring to reflect that both relative and absolute in-root paths are accepted.

### Step 3 — Validate the fix

Run the executor tests:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/node_agent/test_executor.py -q --tb=no
```

Expected: all 21 failures become passes.

## Acceptance Criteria Coverage

| Criterion | How Addressed |
|---|---|
| `_validate_path()` accepts in-root absolute paths | New logic resolves absolute paths and checks `allowed_paths` containment |
| Rejects out-of-root absolute paths | Still rejected — resolved path not relative to any `allowed_paths` root |
| Executor flows (read/write/search/git) work with in-root absolute paths | All flows call `_validate_path()` — they all benefit |
| Trust boundary unchanged | Out-of-bound paths are still rejected; only in-bound absolute paths are newly allowed |
| `pytest tests/node_agent/test_executor.py` exits 0 | Validated in Step 3 |

## Validation Plan

1. Apply the file edit to `executor.py`
2. Run `uv run python -c "from src.node_agent.executor import OperationExecutor"` — must exit 0
3. Run `uv run pytest tests/node_agent/test_executor.py -q --tb=no` — must exit 0 with all 21 tests passing
4. Run `uv run pytest tests/ -q --tb=no` — must not regress other tests (note: some other failures may still exist from EXEC-004/005/006 scope)

## Risks

- **Risk**: Changing path validation could affect other code paths that depend on the "relative only" invariant. **Mitigation**: The docstring is updated; other modules that call `_validate_path` will receive resolved absolute paths which are functionally equivalent for path comparisons.
- **Assumption**: No other code depends on the "relative only" pre-condition. **Confirmation**: The existing tests all use temp directories as `allowed_paths` and pass absolute paths — the current behavior is a bug, not an intentional invariant.
