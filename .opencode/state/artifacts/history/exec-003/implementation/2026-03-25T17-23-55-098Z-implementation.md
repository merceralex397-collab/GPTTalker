# EXEC-003 Implementation: Fix node-agent executor absolute-path validation

## Summary

Fixed `OperationExecutor._validate_path()` in `src/node_agent/executor.py` to accept absolute paths that resolve inside `allowed_paths`, while still rejecting absolute paths that resolve outside those roots.

## File Changes

**File**: `src/node_agent/executor.py`

**Change**: Modified `_validate_path()` (lines 30-68) to allow in-root absolute paths:

```python
def _validate_path(self, path: str) -> Path:
    """
    Validate that a path is within allowed boundaries.

    Args:
        path: Path to validate (relative or absolute, both accepted)

    Returns:
        Resolved absolute path

    Raises:
        PermissionError: If path contains traversal
        PermissionError: If path is not within allowed boundaries
    """
    # Step 1: Resolve path
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        # Absolute path — resolve to real path
        resolved = Path(path).resolve()
    else:
        # Relative path — resolve from current working directory
        resolved = Path.cwd() / path
        resolved = resolved.resolve()

    # Step 2: Check for path traversal in original path
    path_parts = path.replace("\\", "/").split("/")
    if ".." in path_parts:
        raise PermissionError(f"Path traversal is not allowed: {path}")

    # If no allowed paths specified, deny all
    if not self.allowed_paths:
        raise PermissionError("No allowed paths configured")

    # Step 3: Check if resolved path is under any allowed root
    for allowed in self.allowed_paths:
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue

    raise PermissionError(f"Path is outside allowed directories: {path}")
```

**Key changes**:
1. Removed unconditional rejection of absolute paths (was line 44-46)
2. Now resolves absolute paths and checks containment against `allowed_paths`
3. Out-of-bound absolute paths are still rejected via containment check
4. Docstring updated to reflect that both relative and absolute paths are accepted

## Validation Results

### 1. Import test
**Command**: `uv run python -c "from src.node_agent.executor import OperationExecutor"`
**Result**: PASS (exit 0)

### 2. Executor tests
**Command**: `uv run pytest tests/node_agent/test_executor.py -q --tb=no`
**Expected**: All 21 previously-failing tests pass
**Result**: (will be verified after implementation)

### 3. Other tests
**Command**: `uv run pytest tests/ -q --tb=no`
**Expected**: Should not regress tests outside EXEC-003 scope
