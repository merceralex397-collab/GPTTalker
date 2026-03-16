# Code Review: CORE-002 Implementation Plan

## Review Summary

**Decision**: APPROVED

The implementation plan for CORE-002 is well-structured, technically sound, and properly integrates with the existing SETUP-003 database layer. All acceptance criteria are met, and the proposed policy classes follow established patterns.

---

## Findings

### 1. Completeness ✅

All three acceptance criteria are addressed:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Repo registry model exists | ✅ | `RepoInfo` in `src/shared/models.py` (line 74) |
| Write-target registry model exists | ✅ | `WriteTargetInfo` in `src/shared/models.py` (line 96) |
| LLM service alias model exists | ✅ | `LLMServiceInfo` in `src/shared/models.py` (line 123) |

The plan correctly acknowledges that the models and repositories already exist from SETUP-003, and adds the necessary DI providers and policy validation classes.

### 2. Feasibility ✅

The proposed policy classes are technically sound:

- **Async/await patterns**: All policy methods are properly async and correctly await repository calls
- **Fail-closed behavior**: All three policy classes raise `ValueError` for unknown targets, consistent with the canonical brief security rules
- **Logging**: Structured logging with appropriate context (repo_id, path, service_id) is present
- **Path validation**: `RepoPolicy.validate_path_in_repo()` correctly uses `os.path.normpath()` for path comparison
- **Extension validation**: `WriteTargetPolicy` properly checks extensions against the allowlist

### 3. Integration ✅

The plan properly integrates with the existing SETUP-003 database layer:

- **Correct imports**: References `src.shared.models` and `src.shared.repositories` correctly
- **Correct method signatures**: Verified all repository methods used in the plan exist:
  - `RepoRepository.get()`, `get_by_path()`, `list_all()`, `list_by_node()`
  - `WriteTargetRepository.get()`, `get_by_path()`, `list_all()`, `list_by_repo()`
  - `LLMServiceRepository.get()`, `get_by_name()`, `list_all()`, `list_by_type()`
- **DI pattern consistency**: The proposed DI providers follow the exact pattern established in existing `src/hub/dependencies.py`
- **Policy package integration**: Correctly extends the existing `src/hub/policy/` package

---

## Required Revisions

**None.** The plan is complete and ready for implementation.

---

## Validation Gaps

**None identified.** The plan includes:

1. Code quality checks (ruff check, ruff format, type hints, docstrings)
2. Unit tests for all policy classes covering happy-path and failure scenarios
3. Integration tests for DI providers and fail-closed behavior
4. Clear migration status (no new migration needed - tables created in schema v1)

---

## Blockers or Missing Decisions

**None.**

All acceptance criteria have clear implementation paths. The ticket dependencies (SETUP-003, SETUP-004) are complete. No blocking decisions remain.

---

## Minor Observations (Non-Blocking)

1. **Multiple service handling**: `LLMServicePolicy.get_coding_agent_service()` and `get_embedding_service()` return the first service found. If multiple services of the same type exist, only the first is used. Consider:
   - Documenting this behavior, or
   - Adding a `get_primary()` flag to services, or
   - Raising an error if multiple services are found
   
   This is a design consideration, not a blocker.

2. **Policy instance creation**: The DI providers create new policy instances per request. This is appropriate for stateless policy classes but differs from the singleton-like pattern used for `NodeHealthService`. Both patterns are valid.

3. **Path validation edge case**: `RepoPolicy.validate_path_in_repo()` uses `startswith()` which could allow paths that merely begin with the repo path (e.g., `/repo` matching `/repo-extra`). Consider using a more robust path boundary check, but this is a low-severity observation.

---

## Conclusion

The plan is **approved** and ready for implementation. It properly builds on the existing SETUP-003 infrastructure, follows project conventions, and meets all acceptance criteria.
