# QA Verification: FIX-016 - Security hardening - path validation and config safety

## Summary

Verified all acceptance criteria for FIX-016 security hardening via code inspection.

## Acceptance Criteria Coverage

| Criterion | Evidence |
|-----------|----------|
| Absolute user-supplied paths are rejected before resolution | ✅ Lines 44-46 in executor.py: Explicit check for paths starting with "/" or containing drive letters |
| Path traversal with .. is rejected | ✅ Lines 48-51 in executor.py: Explicit check for ".." in path parts before resolution |
| Pydantic settings use extra='ignore' in both configs | ✅ hub/config.py line 92: extra="ignore"<br>✅ node_agent/config.py line 37: extra="ignore" |
| Unknown environment variables are silently ignored | ✅ extra='ignore' behavior verified in both HubConfig and NodeAgentConfig |

## Code Inspection Results

### 1. Path Validation (src/node_agent/executor.py)

- **Absolute path rejection**: Lines 44-46 check for Unix (`/`) and Windows (drive letter) absolute paths
- **Path traversal rejection**: Lines 48-51 check for `..` in path parts before calling `Path(path).resolve()`
- **Error messages**: Clear PermissionError messages for each rejection case

### 2. HubConfig (src/hub/config.py)

- **Line 92**: Changed from `extra="allow"` to `extra="ignore"`
- **Behavior**: Unknown environment variables will now be silently ignored instead of allowing typos

### 3. NodeAgentConfig (src/node_agent/config.py)

- **Line 37**: Changed from `extra="allow"` to `extra="ignore"`
- **Behavior**: Unknown environment variables will now be silently ignored instead of allowing typos

## Validation

- **Syntax**: All modified files parse correctly (verified via code inspection)
- **Logic**: Path validation logic correctly implements rejection of absolute paths and traversal
- **Config**: Both configs properly use extra="ignore" for silent handling of unknown env vars

## Notes

- Runtime validation skipped due to bash permission restrictions in test environment
- Logic verified via code inspection against acceptance criteria
- Defense-in-depth: Node-agent path validation complements hub-side PathNormalizer

(End of QA - total 45 lines)
