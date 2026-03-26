# EXEC-008 Planning Artifact

## Ticket
- **ID:** EXEC-008
- **Title:** Close remaining hub path and write-target security edge cases
- **Wave:** 10
- **Lane:** security
- **Stage:** planning

## Summary
Address 5 pre-existing hub security test failures in test_security.py and test_contracts.py related to path normalization and write-target validation.

## Root Causes and Fixes

### 1. test_path_traversal_dotdot_rejected (test_security.py:60)

**Root Cause:** `PathNormalizer.normalize()` raises `PathTraversalError` with message `"Path '../etc/passwd' escapes base directory '/home/user/repo'"` (path_utils.py:93), but the test asserts `assert "traversal" in str(exc_info.value).lower()`. The word "traversal" does not appear in "escapes base directory".

**Fix:** Update the error message at path_utils.py:93 to include the word "traversal":
- **File:** `src/hub/policy/path_utils.py`
- **Line:** 93
- **Change:** `raise PathTraversalError(f"Path '{path}' escapes base directory '{base}'")`  
  → `raise PathTraversalError(f"Path traversal detected: path '{path}' escapes base directory '{base}'")`

---

### 2. test_home_directory_expansion_rejected (test_security.py:541)

**Root Cause:** `PathNormalizer.normalize()` does NOT reject paths containing `~` home-directory expansion (e.g., `~/../etc/passwd`, `~/.ssh/authorized_keys`, `foo~/bar`). The `~` check exists in `TRAVERSAL_PATTERNS` (line 45) and `validate_no_traversal()` (lines 111-118), but the check happens on the normalized path AFTER `.resolve()` has already resolved `~` to an actual home directory path. By the time validation runs, `~` has been expanded away and is no longer present in the path string.

**Fix:** Add `~` detection BEFORE `.resolve()` expansion in the normalize() method:
- **File:** `src/hub/policy/path_utils.py`
- **Location:** In the `normalize()` method, before the Path.join/resolve calls (around line 70-71)
- **Change:** Add explicit `~` rejection before Path resolution:
  ```python
  # Reject home directory expansion before normalize (resolve expands ~)
  if "~" in path:
      path_parts = path.replace("\\", "/").split("/")
      if "~" in path_parts:
          raise PathTraversalError(f"Path traversal detected: '~' in path '{path}'")
  ```

---

### 3. test_unregistered_write_target_denied (test_security.py:213)

**Root Cause:** The test creates `mock_repo = MagicMock()` and sets `mock_repo.get = AsyncMock(return_value=None)`, but the code in `WriteTargetPolicy.validate_write_access()` calls `await self._repo.get_by_path(path)` (line 38 of write_target_policy.py). The mock has `.get` configured but not `.get_by_path`, so when the code calls `get_by_path`, it returns a non-awaitable MagicMock that causes `TypeError: object MagicMock can't be used in 'await' expression`.

**Fix:** This is a TEST bug. The brief constraint says "Do NOT change test files except for the fixture fix in test_write_markdown_validates_extension". The test_unregistered_write_target_denied test is NOT listed as an allowed test change, so this failure is OUT OF SCOPE for EXEC-008. The test mocks `.get` but the code calls `.get_by_path`.

---

### 4. test_invalid_path_rejected (test_contracts.py:857)

**Root Cause:** `read_repo_file_handler()` calls `PathNormalizer.validate_no_traversal(file_path)` on the ORIGINAL file_path BEFORE normalization (inspection.py:253). For input `foo/./bar`:
1. `validate_no_traversal("foo/./bar")` is called first
2. The method splits on `/` getting `["foo", ".", "bar"]`
3. `..` and `~` are checked - neither found in path_parts
4. Validation passes
5. `normalize("foo/./bar", repo_path)` is called
6. After normalize, path becomes `foo/bar` which is inside the repo - no error

The issue is that `.` components in the path should be normalized before the boundary check. The `normalize()` function DOES handle `.` correctly via `Path.resolve()`, but the problem is the `validate_no_traversal()` check runs on the pre-normalized path.

**Fix:** In `read_repo_file_handler()` (inspection.py:253-255), move the `validate_no_traversal` call to AFTER the `normalize()` call, so it validates the normalized path:
- **File:** `src/hub/tools/inspection.py`
- **Lines:** 251-262
- **Change:** Currently:
  ```python
  try:
      # Validate path doesn't contain traversal attempts
      PathNormalizer.validate_no_traversal(file_path)
      # Normalize path relative to repo root
      normalized_path = PathNormalizer.normalize(file_path, repo_path)
  except PathTraversalError as e:
  ```
  Should be:
  ```python
  try:
      # Normalize path relative to repo root
      normalized_path = PathNormalizer.normalize(file_path, repo_path)
      # Validate normalized path doesn't contain traversal attempts
      PathNormalizer.validate_no_traversal(normalized_path)
  except PathTraversalError as e:
  ```

Note: This change is safe because `normalize()` already performs traversal checks internally (path_utils.py:83-93) and raises PathTraversalError if the path escapes base. The additional `validate_no_traversal` on the normalized path is redundant but ensures the error message contains "traversal".

---

### 5. test_write_markdown_validates_extension (test_contracts.py:562)

**Root Cause:** The test creates local mocks without properly using the `mock_write_target` fixture. The test does NOT include `mock_write_target` as a fixture parameter in its function signature, so when it references `mock_write_target` in the body at line 557, it's getting the fixture function object itself, not the fixture's return value (a MagicMock with `allowed_extensions`).

Looking at the test (lines 545-574):
```python
async def test_write_markdown_validates_extension(
    self,
    mock_node_client,
    mock_node,
    mock_repo_repo,
):  # <-- missing mock_write_target parameter
    ...
    mock_write_target_policy.list_write_targets_for_repo = AsyncMock(
        return_value=[mock_write_target]  # <-- this is the fixture function, not the mock
    )
```

**Fix (test fixture):** Add `mock_write_target` to the test function parameters so pytest injects the fixture's return value:
```python
async def test_write_markdown_validates_extension(
    self,
    mock_node_client,
    mock_node,
    mock_repo_repo,
    mock_write_target,  # <-- ADD THIS
):
```

---

## Implementation Steps

### Step 1: Fix PathNormalizer error message (path_utils.py:93)
- Change "escapes base directory" message to include "traversal"

### Step 2: Add ~ detection before resolve (path_utils.py:70-71)  
- Add explicit ~ check before Path.join/resolve in normalize()

### Step 3: Fix read_repo_file_handler validation order (inspection.py:251-262)
- Reorder to call normalize() before validate_no_traversal()

### Step 4: Fix test fixture for write_markdown (test_contracts.py:545-574)
- Add `mock_write_target` to the test function parameters

---

## Files to Modify

| File | Change |
|------|--------|
| `src/hub/policy/path_utils.py` | Fix error message (line 93), add ~ rejection (around line 70) |
| `src/hub/tools/inspection.py` | Reorder normalize/validate_no_traversal calls (lines 251-262) |
| `tests/hub/test_contracts.py` | Fix test_write_markdown_validates_extension fixture usage |

---

## Validation Plan

Run the following to verify fixes:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no -k "test_path_traversal_dotdot_rejected or test_home_directory_expansion_rejected"
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -q --tb=no -k "test_invalid_path_rejected or test_write_markdown_validates_extension"
```

Full acceptance:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no
```

---

## Blockers

1. **test_unregistered_write_target_denied**: The brief explicitly says not to change test files except for `test_write_markdown_validates_extension`. This test failure is NOT in scope for EXEC-008. The test mocks `.get` but the code calls `.get_by_path` - this is a test/code mismatch that requires either test change (not allowed) or code change (would break real functionality).

2. **EXEC-008 scope after blocker #1**: If test_unregistered_write_target_denied cannot be fixed due to the constraint, we need to clarify whether EXEC-008's acceptance criteria can still be met with 4/5 failures fixed, or if this ticket needs to be re-scoped.
