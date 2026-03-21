# Implementation: FIX-016 - Security hardening - path validation and config safety

## Summary

Implemented security hardening fixes for two identified security issues:
1. Added explicit path validation to reject absolute paths and path traversal in node-agent executor
2. Changed Pydantic config from `extra="allow"` to `extra="ignore"` in both hub and node-agent configs

## Changes Made

### 1. Path Validation (src/node_agent/executor.py)

Modified `_validate_path` method (lines 30-68) to add explicit security checks before path resolution:

- **Reject absolute paths**: Added check `if path.startswith("/") or (len(path) > 1 and path[1] == ":")` to reject Unix absolute paths and Windows drive letters
- **Reject path traversal**: Added explicit check for `..` in path parts before any resolution: `if ".." in path_parts`
- **Preserve existing behavior**: After validation checks, continues with existing resolution and boundary checks

```python
def _validate_path(self, path: str) -> Path:
    # Step 1: Reject absolute paths
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        raise PermissionError(f"Absolute paths are not allowed: {path}")

    # Step 2: Explicitly reject path traversal before any resolution
    path_parts = path.replace("\\", "/").split("/")
    if ".." in path_parts:
        raise PermissionError(f"Path traversal is not allowed: {path}")

    # Step 3: Continue with existing resolution logic
    resolved = Path(path).resolve()
    # ... (existing boundary checks)
```

### 2. HubConfig Safety (src/hub/config.py)

Changed line 92 from `extra="allow"` to `extra="ignore"`:

```python
model_config = SettingsConfigDict(
    env_prefix="GPTTALKER_",
    extra="ignore",  # FIXED: unknown env vars silently ignored
    case_sensitive=False,
)
```

### 3. NodeAgentConfig Safety (src/node_agent/config.py)

Changed line 37 from `extra="allow"` to `extra="ignore"`:

```python
model_config = SettingsConfigDict(
    env_prefix="GPTTALKER_NODE_",
    extra="ignore",  # FIXED: unknown env vars silently ignored
    case_sensitive=False,
)
```

## Validation

All edits verified by code inspection:
- Syntax validation: Files parse correctly
- Path validation: Explicit checks added before resolution
- Config safety: extra="ignore" set in both HubConfig and NodeAgentConfig

## Acceptance Criteria Coverage

| Criterion | Status |
|-----------|--------|
| Absolute user-supplied paths are rejected before resolution | ✅ Implemented via explicit check in _validate_path |
| Path traversal with .. is rejected | ✅ Explicit check added before resolution |
| Pydantic settings use extra='ignore' in both configs | ✅ Changed in HubConfig and NodeAgentConfig |
| Unknown environment variables are silently ignored | ✅ extra='ignore' behavior |

## Files Modified

| File | Change |
|------|--------|
| `src/node_agent/executor.py` | Added absolute path and traversal rejection to `_validate_path` |
| `src/hub/config.py` | Changed `extra="allow"` to `extra="ignore"` in HubConfig |
| `src/node_agent/config.py` | Changed `extra="allow"` to `extra="ignore"` in NodeAgentConfig |

## Risks and Mitigation

- **Risk**: Some existing code might rely on passing absolute paths to executor
- **Mitigation**: Node agent executor is only called with relative paths from hub-side handlers that already normalize paths via PathNormalizer
- **Defense-in-depth**: This change adds a second layer of validation at the node agent layer

(End of implementation - total 85 lines)
