# Review: FIX-016 - Security hardening - path validation and config safety

## Decision: APPROVED

## Summary

The plan correctly identifies two security issues and provides accurate implementation steps to fix them. All acceptance criteria are addressed.

## Findings

### 1. Path Validation (src/node_agent/executor.py)

**Current state verified**: Lines 30-57 show `_validate_path` method that:
- Calls `Path(path).resolve()` which handles `..` implicitly
- Does NOT explicitly reject absolute paths before resolution
- Only checks boundaries after resolution

**Plan accuracy**: ✅ Correct
- The plan correctly identifies that absolute paths should be rejected before resolution
- The proposed code adds explicit checks for:
  - Unix absolute paths (`/`)
  - Windows drive letters (`C:`, etc.)
  - Path traversal (`..`) before resolution

### 2. Config Safety (HubConfig and NodeAgentConfig)

**Current state verified**:
- `src/hub/config.py` line 92: `extra="allow"` ✅
- `src/node_agent/config.py` line 37: `extra="allow"` ✅

**Plan accuracy**: ✅ Correct
- Plan correctly identifies both locations use `extra="allow"`
- Change to `extra="ignore"` will silently ignore unknown env vars (per acceptance criteria)

## Acceptance Criteria Coverage

| Criterion | Status |
|-----------|--------|
| Absolute user-supplied paths are rejected before resolution | ✅ Addressed - explicit check added |
| Path traversal with .. is rejected | ✅ Addressed - explicit `..` check added |
| Pydantic settings use extra='ignore' in both configs | ✅ Addressed - both configs changed |
| Unknown environment variables are silently ignored | ✅ Addressed - extra='ignore' behavior |

## Validation Plan

The plan includes appropriate validation steps:
- Syntax validation with py_compile
- Import tests
- Path validation tests (absolute, traversal, valid relative)
- Config validation for unknown env vars
- Linting with ruff

## Risks and Mitigations

**Risk noted**: Some existing code might rely on passing absolute paths to executor.

**Mitigation in plan**: Path validation at hub side (PathNormalizer) provides first-layer defense. This change adds defense-in-depth at node agent layer.

This is appropriate - the node agent should receive relative paths from hub-side handlers.

## No Issues Found

The plan is complete, feasible, and correctly addresses all acceptance criteria.
