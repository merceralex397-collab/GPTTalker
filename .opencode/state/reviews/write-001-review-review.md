# Code Review: WRITE-001 - write_markdown with atomic scoped writes

**Ticket**: WRITE-001  
**Title**: write_markdown with atomic scoped writes  
**Stage**: review  
**Reviewer**: gpttalker-reviewer-code  
**Date**: 2026-03-16

---

## Summary

Implementation is **APPROVED**. All three acceptance criteria are satisfied with correct policy integration, atomic write behavior, and verification metadata.

---

## Acceptance Criteria Verification

### 1. Writes are restricted to approved targets ✅

**Evidence**:
- **Hub handler** (`src/hub/tools/markdown.py` lines 92-112): Retrieves write targets via `write_target_policy.list_write_targets_for_repo(repo_id)` and rejects if none exist
- **Extension validation** (lines 114-136): Checks file extension against `target.allowed_extensions` for the matched write target
- **Path traversal prevention** (lines 138-147): Uses `PathNormalizer.validate_no_traversal(path)` to block `..` and escape attempts
- **Write access validation** (lines 164-174): Calls `write_target_policy.validate_write_access(normalized_path, extension)` which raises `ValueError` for unknown paths or disallowed extensions (fail-closed in `src/hub/policy/write_target_policy.py` lines 38-56)

### 2. Atomic write behavior is explicit ✅

**Evidence**:
- **Node agent executor** (`src/node_agent/executor.py` lines 392-464): 
  - Line 423-425: Computes SHA256 hash before writing
  - Lines 427-438: Writes to temp file using `tempfile.NamedTemporaryFile` with prefix `.filename.` and suffix `.tmp`
  - Line 444: Uses `os.replace(tmp_path, validated_path)` for atomic filesystem rename
  - Lines 461-471: Error handling cleans up temp file on failure
- **HTTP endpoint** (`src/node_agent/routes/operations.py` lines 323-330): Docstring explicitly documents the atomic write pattern

### 3. Write responses include verification metadata ✅

**Evidence**:
- **Hub response** (`src/hub/tools/markdown.py` lines 200-222):
  ```python
  {
      "success": True,
      "repo_id": repo_id,
      "node_id": node_id,
      "path": normalized_path,
      "bytes_written": data.get("bytes_written", 0),
      "sha256_hash": data.get("sha256_hash", ""),
      "verified": data.get("verified", False),
      "content_hash_algorithm": data.get("content_hash_algorithm", "sha256"),
  }
  ```
- **Node agent response** (`src/node_agent/executor.py` lines 453-458): Returns `sha256_hash`, `verified`, and `content_hash_algorithm`

---

## Policy Integration

### WRITE_REQUIREMENT applied ✅

- **Registration** (`src/hub/tools/__init__.py` lines 268-302): `write_markdown` tool registered with `policy=WRITE_REQUIREMENT`
- **Policy definition** (`src/hub/tool_routing/requirements.py` lines 145-150):
  ```python
  WRITE_REQUIREMENT = PolicyRequirement(
      scope=OperationScope.WRITE,
      requires_node=True,
      requires_write_target=True,
  )
  ```
- **Router validation** (`src/hub/tool_routing/policy_router.py` lines 224-230): Calls `_validate_write_target()` when `requires_write_target=True`
- **DI injection** (`src/hub/dependencies.py` lines 350-378): `write_target_repo` and `write_target_policy` properly injected into PolicyAwareToolRouter

---

## Code Quality Observations

| Aspect | Status | Notes |
|--------|--------|-------|
| Type hints | ✅ Complete | All functions have type annotations |
| Docstrings | ✅ Present | All handlers have detailed docstrings |
| Error handling | ✅ Robust | Graceful degradation with structured errors |
| Logging | ✅ Structured | Trace ID, tool_name, outcome, duration captured |
| Fail-closed | ✅ Enforced | Unknown targets/paths rejected explicitly |

---

## Low-Severity Observations

1. **Line 165-166 in markdown.py**: The policy router already validates write target before handler execution via `WRITE_REQUIREMENT`. The handler then validates again via `write_target_policy.validate_write_access()`. This is defensive but could be considered redundant - not a blocker.

2. **Extension extraction**: The `_get_extension()` helper extracts extension without leading dot, but the comparison at line 120 `if extension in target.allowed_extensions` assumes consistency with how extensions are stored. The codebase appears consistent - not a blocker.

---

## Regression Risk

**Low**. The implementation:
- Uses existing patterns from similar tools (REPO-002, REPO-003)
- Properly integrates with established policy engine
- Follows the atomic write pattern used in other write operations
- Does not modify any shared infrastructure that could affect other tools

---

## Test Gaps

No blocking gaps identified. The implementation would benefit from:
- Unit test for `write_markdown_handler` with mocked dependencies
- Integration test for atomic write verification
- Error path test for extension rejection

---

## Decision

**APPROVED** - Ready to advance to QA stage.
