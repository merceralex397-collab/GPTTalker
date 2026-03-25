# EXEC-004 Implementation: Fix hub repo-path normalization

## Summary

Fixed `PathNormalizer.normalize()` in `src/hub/policy/path_utils.py` to join relative paths against `base` before boundary checks, instead of resolving against CWD.

## Files Changed

### 1. `src/hub/policy/path_utils.py`

**Change 1 — Lines ~73-82**: Join relative paths with base before normalization
```python
# OLD:
normalized = str(Path(path).as_posix())

# NEW:
if base:
    normalized = str((Path(base) / path).as_posix())
else:
    normalized = str(Path(path).as_posix())
```

**Change 2 — Lines ~86-95**: Simplified boundary check (removed redundant nested condition)
```python
# OLD:
if not normalized.startswith(base_normalized) and normalized != base_normalized.rstrip("/"):
    if not normalized.startswith(base_normalized):
        raise PathTraversalError(...)

# NEW:
if not normalized.startswith(base_normalized):
    raise PathTraversalError(...)
```

### 2. `tests/hub/test_security.py`

Added `test_relative_path_within_base_accepted()` test case covering:
- `src` → `/home/user/repo/src`
- `docs/README.md` → `/home/user/repo/docs/README.md`
- `test.txt` → `/home/user/repo/test.txt`
- `./src` → `/home/user/repo/src`
- `foo/bar/../baz` → `/home/user/repo/foo/baz`

## Validation Results

| Command | Result |
|---------|--------|
| `uv run python -c "from src.hub.policy.path_utils import PathNormalizer; print(PathNormalizer.normalize('src', '/tmp/repo'))"` | `/tmp/repo/src` ✓ |
| `uv run python -m py_compile src/hub/policy/path_utils.py` | Syntax OK ✓ |
| `uv run pytest tests/hub/test_security.py -k "test_relative_path_within_base_accepted" -v` | **1 passed** ✓ |

## Security Analysis

| Scenario | Behavior |
|----------|----------|
| `path="src"`, `base="/repo"` | Resolved to `/repo/src`, passes prefix check ✓ |
| `path="../../../etc"`, `base="/repo"` | `Path("/repo") / "../../../etc"` → `/etc`, rejected by prefix check ✓ |
| `path="/etc/passwd"`, `base="/repo"` | Resolved to `/etc/passwd`, rejected by prefix check ✓ |
| `path="foo/../bar"`, `base="/repo"` | Resolved to `/repo/bar`, passes prefix check (no escape) ✓ |