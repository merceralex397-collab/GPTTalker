# Code Review: REPO-003 - search_repo and git_status tools

**Ticket**: REPO-003  
**Title**: search_repo and git_status tools  
**Review Stage**: review  
**Decision**: APPROVED

## Summary

Implementation of REPO-003 is **APPROVED**. All three acceptance criteria are met with strong security controls. The implementation follows established patterns from REPO-002 and integrates properly with the policy engine.

## Acceptance Criteria Verification

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| Search uses bounded ripgrep execution | ✅ | Path validation at hub (PathNormalizer) and node (_validate_path), ripgrep via subprocess with timeout, include_patterns filtering |
| Git status is exposed read-only | ✅ | Only `git status --porcelain`, `git branch --show-current`, `git rev-list` - all read-only |
| Timeout and error handling are explicit | ✅ | Search: 60s default, 120s max. Git: 30s default, 60s max. Proper timeout handling in subprocess |

## Detailed Findings

### Security Controls (Strong)

1. **Path Validation - Hub Side** (`search.py` lines 110-121):
   - Uses `PathNormalizer.validate_no_traversal()` to reject `..`, symlink escapes
   - Normalizes path relative to repo root before sending to node
   - Validates node exists and repo belongs to specified node

2. **Path Validation - Node Side** (`executor.py` lines 30-57):
   - `_validate_path()` checks path is within `allowed_paths`
   - If no allowed paths configured, denies all access
   - Resolves symlinks before validation

3. **Bounded Ripgrep Execution** (`executor.py` lines 150-265):
   - Uses `asyncio.create_subprocess_exec` with ripgrep
   - Timeout enforced via `asyncio.wait_for(proc.communicate(), timeout=timeout)`
   - Process killed on timeout to prevent runaway execution
   - `max_results` capped at 1000 to limit response size

4. **Read-Only Git Operations** (`executor.py` lines 267-390):
   - `git status --porcelain` - read only
   - `git branch --show-current` - read only
   - `git rev-list --left-right --count` - read only
   - No `git commit`, `git push`, or other write operations

5. **Policy Integration** (`tools/__init__.py`):
   - Both tools registered with `policy=READ_REPO_REQUIREMENT`
   - Proper node/repo validation in handlers

### Code Quality (High)

1. **Type Hints**: Complete coverage in all new files
2. **Structured Logging**: Consistent with project conventions using trace_id, node_id, repo_id
3. **Error Handling**: Graceful degradation with informative error messages
4. **Input Validation**: Limits enforced (max_results ≤ 1000, timeout ≤ 120/60)

### Minor Observations

| Severity | Issue | Location | Notes |
|----------|-------|----------|-------|
| Low | No trace_id passed to node | node_client.py:236-278 | Could help with request correlation |
| Low | Unused datetime import removal noted | Implementation summary | Was cleaned up |

### Risk Assessment

- **Regression Risk**: Low - implementation follows established REPO-002 patterns
- **Security Risk**: Low - fail-closed path validation at both layers
- **Validation Gap**: None - all acceptance criteria verified

## Files Reviewed

| File | Purpose | Key Checks |
|------|---------|------------|
| `src/hub/tools/search.py` | Hub search handler | Path validation, policy enforcement, timeout clamping |
| `src/hub/tools/git_operations.py` | Hub git status handler | Node/repo validation, read-only operations |
| `src/node_agent/executor.py` | Node execution layer | Path boundary checks, subprocess timeout, ripgrep/git commands |
| `src/node_agent/routes/operations.py` | Node HTTP endpoints | Request validation, error handling |
| `src/hub/tools/__init__.py` | Tool registration | Policy requirements |
| `src/hub/services/node_client.py` | Hub-to-node client | Method signatures, timeout passing |

## Conclusion

The implementation is production-ready. All acceptance criteria are satisfied with strong security controls:

1. ✅ Bounded ripgrep execution with path validation and timeout
2. ✅ Read-only git operations (status, branch, rev-list only)
3. ✅ Explicit timeout handling with configurable limits
4. ✅ READ_REPO_REQUIREMENT policy integration

**Recommendation**: Advance to QA stage.

---
*Reviewer: gpttalker-reviewer-code*  
*Date: 2026-03-16*  
*Artifact: .opencode/state/reviews/repo-003-review-review.md*
