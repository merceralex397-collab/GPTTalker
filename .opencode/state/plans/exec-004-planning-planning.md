# EXEC-004 Planning — Fix hub repo-path normalization for inspection and file-read flows

## 1. Scope

**Ticket**: EXEC-004  
**Title**: Fix hub repo-path normalization for inspection and file-read flows  
**Stage**: planning  
**Lane**: bugfix  

## 2. Files and Systems Affected

| File | Change |
|------|--------|
| `src/hub/policy/path_utils.py` | Fix `normalize()` to join relative paths with `base` before boundary check |

No other files need changes. Callers in `inspection.py` (lines 98, 242) and `search.py` (line 121) already pass `repo_path` as `base` correctly; the bug is entirely in `normalize()`.

## 3. Root Cause

`PathNormalizer.normalize()` at line 76 does:

```python
normalized = str(Path(path).as_posix())
```

When `path` is a relative user-supplied path like `"src"` and `base` is an absolute repo path like `"/tmp/test_repo"`:

1. `Path("src").as_posix()` → `"src"` (resolved against CWD, not against `base`)
2. Boundary check: `"src".startswith("/tmp/test_repo/")` → `False`
3. Error raised: `"Path 'src' escapes base directory '/tmp/test_repo'"`

This breaks inspection and file-read for all relative paths (`"src"`, `"test.txt"`, `"docs/README.md"`, etc.).

## 4. Implementation Steps

### Step 1 — Fix `normalize()` in `path_utils.py`

**Location**: `src/hub/policy/path_utils.py`, lines 73–94

**Before** (lines 73–78):
```python
        # Normalize the path
        try:
            # Use Path for normalization (handles .., ., multiple slashes)
            normalized = str(Path(path).as_posix())
        except (ValueError, OSError) as e:
            raise PathTraversalError(f"Invalid path: {path}") from e
```

**After**:
```python
        # Normalize the path
        try:
            # Use Path for normalization (handles .., ., multiple slashes)
            if base:
                # Join relative paths to base; absolute paths override base
                normalized = str((Path(base) / path).as_posix())
            else:
                normalized = str(Path(path).as_posix())
        except (ValueError, OSError) as e:
            raise PathTraversalError(f"Invalid path: {path}") from e
```

**Rationale**: When `base` is provided and `path` is relative (does not start with `/`), joining before normalization ensures the path is resolved against the repo root. `Path(base) / path` handles `..` components correctly through the existing normalization.

### Step 2 — Simplify the boundary-check block (lines 80–93)

**Before**:
```python
        # If base is provided, ensure the normalized path is within base
        if base:
            base_normalized = str(Path(base).as_posix())
            # Ensure base ends with separator for proper prefix matching
            if not base_normalized.endswith("/"):
                base_normalized += "/"

            if not normalized.startswith(base_normalized) and normalized != base_normalized.rstrip(
                "/"
            ):
                # Check if it's a direct child
                if not normalized.startswith(base_normalized):
                    raise PathTraversalError(f"Path '{path}' escapes base directory '{base}'")
```

**After**:
```python
        # If base is provided, ensure the normalized path is within base
        if base:
            base_normalized = str(Path(base).as_posix())
            # Ensure base ends with separator for proper prefix matching
            if not base_normalized.endswith("/"):
                base_normalized += "/"

            if not normalized.startswith(base_normalized):
                raise PathTraversalError(f"Path '{path}' escapes base directory '{base}'")
```

**Rationale**: The original `and normalized != base_normalized.rstrip("/")` branch and the duplicate inner `if not normalized.startswith(base_normalized)` check are redundant. After joining, `normalized` is guaranteed to be within `base` if the prefix check passes.

## 5. Security Analysis

| Scenario | Old Behavior | New Behavior |
|----------|-------------|-------------|
| `path="src"`, `base="/repo"` | ❌ Rejected (false positive) | ✅ Resolved to `/repo/src`, passes prefix check |
| `path="../../../etc"`, `base="/repo"` | ✅ Rejected by `validate_no_traversal()` | ✅ `Path("/repo") / "../../../etc"` → `/etc`, rejected by prefix check |
| `path="/etc/passwd"`, `base="/repo"` | ✅ Rejected | ✅ Resolved to `/etc/passwd`, rejected by prefix check (still correct) |
| `path="foo/../bar"`, `base="/repo"` | ✅ Rejected by `validate_no_traversal()` | ✅ `Path("/repo") / "foo/../bar"` → `/repo/bar`, passes prefix check (correct — no escape) |
| Symlink escape | ✅ Caught by `validate_symlinks()` | ✅ Unchanged — `validate_symlinks()` still runs independently |

**Traversal still rejected**: `validate_no_traversal()` is called before the join (line 71), so `..` patterns in the user-provided `path` are caught and rejected before `base` is consulted.

**Absolute paths still rejected**: An absolute path like `/etc/passwd` joined to `base` produces `/etc/passwd` (the absolute path overrides), which then fails the prefix check against `base`.

**Symlink escapes**: `validate_symlinks()` is a separate method called by callers, not part of `normalize()`. This is unchanged.

## 6. Test Updates

### New test case in `tests/hub/test_security.py`

Add to `TestPathNormalization` class (around line 97, after `test_path_traversal_absolute_path_rejected`):

```python
def test_relative_path_within_base_accepted(self):
    """Test that relative paths are resolved against base."""
    base = "/home/user/repo"
    
    # Valid relative paths should be resolved and accepted
    valid_relative = [
        ("src", "/home/user/repo/src"),
        ("docs/README.md", "/home/user/repo/docs/README.md"),
        ("test.txt", "/home/user/repo/test.txt"),
        ("./src", "/home/user/repo/src"),
        ("foo/bar/../baz", "/home/user/repo/foo/baz"),
    ]
    
    for path, expected in valid_relative:
        result = PathNormalizer.normalize(path, base)
        assert result == expected, f"Expected {expected}, got {result}"
```

### Existing tests — no changes needed

The test `test_path_traversal_absolute_path_rejected` (line 77–96) verifies that absolute paths outside base are rejected. This behavior is preserved because `Path(base) / "/abs/path"` = `/abs/path`.

## 7. Validation Plan

### Step 1 — Syntax and import validation
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile src/hub/policy/path_utils.py
```

### Step 2 — Unit-level path normalization tests
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -k "test_relative_path_within_base_accepted or test_path_traversal_absolute_path_rejected" -v
```

### Step 3 — Full contract and security test suite
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_security.py -q --tb=short
```

### Step 4 — All hub tests
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/ -q --tb=short
```

## 8. Other Methods with Same Issue

**Checked**: `is_safe_relative()`, `validate_symlinks()`, `build_safe_path()`

- `is_safe_relative()` (line 127) calls `normalize(path, base)` internally, so it benefits from the fix automatically.
- `validate_symlinks()` (line 150) uses `Path.resolve()` on the raw `path` and `base`, but this is separate from `normalize()` and operates on already-joined paths from callers.
- `build_safe_path()` (line 258) explicitly joins parts with `base` using `Path(base).joinpath(*parts)` before calling `normalize(combined, base)`, so it is correct.

No other methods in `path_utils.py` require changes.

## 9. Risks and Assumptions

| Risk | Mitigation |
|------|------------|
| Changing normalize() could break callers that expect the old behavior | Only `inspection.py`, `search.py`, and `markdown.py` call `normalize()` with a repo `base`; all were broken by the bug and will improve |
| The `..` traversal check happens before join, which is correct order | `validate_no_traversal()` on the raw user path catches `..` before `base` is consulted |

## 10. Decision Blockers

None. All information needed is present in the diagnosis pack and codebase.

## 11. Acceptance Criteria Checklist

| # | Criterion | How Verified |
|---|-----------|--------------|
| 1 | Repo-relative paths normalize against repo base | Unit test `test_relative_path_within_base_accepted` |
| 2 | Valid inspection/file-read no longer fail for in-repo relative paths | `test_contracts.py` inspection/file-read cases pass |
| 3 | Acceptance test suite passes | `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_security.py -q --tb=no` |
| 4 | Traversal, absolute, and symlink escapes still rejected | Existing tests + new negative test cases |
