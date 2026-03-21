# Plan: FIX-016 - Security hardening - path validation and config safety

## Summary

Two security issues need fixing:
1. `_validate_path` in node-agent accepts absolute paths instead of rejecting them as user input
2. HubConfig and NodeAgentConfig use `extra='allow'` which hides typos in environment variables

## Current State Analysis

### 1. Path Validation Issue (src/node_agent/executor.py)

**Current implementation** (lines 30-57):
- `_validate_path(path)` accepts any path string
- Calls `Path(path).resolve()` which handles `..` but doesn't explicitly reject absolute paths
- Only checks if resolved path is within allowed boundaries
- **Problem**: Accepts absolute paths as user input without explicit rejection

**Required behavior per spec**: User-supplied paths should be relative (relative to configured allowed paths), not absolute.

### 2. Config Safety Issue

**HubConfig** (src/hub/config.py, line 92):
```python
model_config = SettingsConfigDict(
    env_prefix="GPTTALKER_",
    extra="allow",  # ISSUE: allows typos in env vars
    case_sensitive=False,
)
```

**NodeAgentConfig** (src/node_agent/config.py, line 37):
```python
model_config = SettingsConfigDict(
    env_prefix="GPTTALKER_NODE_",
    extra="allow",  # ISSUE: allows typos in env vars
    case_sensitive=False,
)
```

`extra="allow"` silently accepts unknown environment variables, hiding typos. Should be `extra="ignore"`.

## Implementation Steps

### Step 1: Fix Path Validation in Node Agent (src/node_agent/executor.py)

Modify `_validate_path` method to:
1. **Reject absolute paths** - Check if path starts with `/` (Unix) or has drive letter (Windows) and reject with clear error
2. **Reject path traversal** - Explicitly check for `..` before resolution
3. **Preserve existing behavior** - After validation, continue with existing resolution and boundary checks

**Changes to _validate_path (lines 30-57)**:
```python
def _validate_path(self, path: str) -> Path:
    """Validate that a path is within allowed boundaries.
    
    Args:
        path: Path to validate (must be relative, not absolute)
        
    Returns:
        Resolved absolute path
        
    Raises:
        PermissionError: If path is absolute or contains traversal
        PermissionError: If path is not within allowed boundaries
    """
    # Step 1: Reject absolute paths
    if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
        raise PermissionError(f"Absolute paths are not allowed: {path}")
    
    # Step 2: Explicitly reject path traversal before any resolution
    path_parts = path.replace('\\', '/').split('/')
    if '..' in path_parts:
        raise PermissionError(f"Path traversal is not allowed: {path}")
    
    # Step 3: Continue with existing resolution logic
    resolved = Path(path).resolve()
    
    # If no allowed paths specified, deny all
    if not self.allowed_paths:
        raise PermissionError("No allowed paths configured")
    
    # Check if path is under any allowed path
    for allowed in self.allowed_paths:
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue
    
    raise PermissionError(f"Path not within allowed boundaries: {path}")
```

### Step 2: Fix HubConfig (src/hub/config.py)

Change line 92 from `extra="allow"` to `extra="ignore"`:
```python
model_config = SettingsConfigDict(
    env_prefix="GPTTALKER_",
    extra="ignore",  # FIXED: unknown env vars silently ignored
    case_sensitive=False,
)
```

### Step 3: Fix NodeAgentConfig (src/node_agent/config.py)

Change line 37 from `extra="allow"` to `extra="ignore"`:
```python
model_config = SettingsConfigDict(
    env_prefix="GPTTALKER_NODE_",
    extra="ignore",  # FIXED: unknown env vars silently ignored
    case_sensitive=False,
)
```

## Files Modified

| File | Change |
|------|--------|
| `src/node_agent/executor.py` | Add absolute path and traversal rejection to `_validate_path` |
| `src/hub/config.py` | Change `extra="allow"` to `extra="ignore"` in HubConfig |
| `src/node_agent/config.py` | Change `extra="allow"` to `extra="ignore"` in NodeAgentConfig |

## Validation Plan

1. **Syntax validation**: `python3 -m py_compile src/node_agent/executor.py src/hub/config.py src/node_agent/config.py`
2. **Import test**: `python3 -c "from src.node_agent.executor import OperationExecutor; from src.hub.config import HubConfig; from src.node_agent.config import NodeAgentConfig"`
3. **Path validation tests**:
   - Test absolute path rejection: `_validate_path("/etc/passwd")` raises PermissionError
   - Test traversal rejection: `_validate_path("../etc/passwd")` raises PermissionError  
   - Test valid relative path works: `_validate_path("subdir/file.txt")` returns resolved Path
4. **Config validation**: Verify unknown env vars are silently ignored (no error raised)
5. **Linting**: `ruff check src/node_agent/executor.py src/hub/config.py src/node_agent/config.py`

## Acceptance Criteria Coverage

| Criterion | Status |
|-----------|--------|
| Absolute user-supplied paths are rejected before resolution | ✅ Implemented via explicit check in _validate_path |
| Path traversal with .. is rejected | ✅ Explicit check added before resolution |
| Pydantic settings use extra='ignore' in both configs | ✅ Changed in HubConfig and NodeAgentConfig |
| Unknown environment variables are silently ignored | ✅ extra='ignore' behavior |

## Risks and Assumptions

- **Risk**: Some existing code might rely on passing absolute paths to executor. Need to verify no breakage.
- **Assumption**: Node agent executor is only called with relative paths from hub-side handlers that already normalize.
- **Mitigation**: The path validation at hub side (PathNormalizer) should continue to provide first-layer defense.

## Integration Points

- Hub-side PathNormalizer already validates paths before sending to node agent
- This change adds defense-in-depth at node agent layer
- No changes needed to tool handlers or other services
