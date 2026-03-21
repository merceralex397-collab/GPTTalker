# Implementation: FIX-008 - Add recent_commits to git_status output

## Summary
Added `recent_commits` field to git_status output with the last 10 commits (hash, author, date, message).

## Changes Made

### 1. src/node_agent/executor.py
- Added git log command to retrieve last 10 commits inside `git_status()` method
- Uses `git log -10 --pretty=format:%H|%an|%aI|%s` to get:
  - `%H` - Full commit hash (truncated to 8 chars in output)
  - `%an` - Author name
  - `%aI` - Author date (ISO 8601 format)
  - `%s` - Commit subject/message
- Parses output and builds list of dicts with: `hash`, `author`, `date`, `message`
- Added to return value under key `recent_commits`
- Gracefully handles failures (empty list returned if git log fails)

### 2. src/hub/tools/git_operations.py
- Added `recent_commits` field to the response dictionary
- Retrieves from node agent result: `result.get("recent_commits", [])`

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| git_status response includes recent_commits array | ✅ Added |
| Each commit entry has hash, author, date, and message fields | ✅ Implemented |
| Default returns last 10 commits | ✅ Default is -10 |

## Notes
- The git log command uses ISO 8601 date format (`%aI`) for consistent parsing
- If git log fails (e.g., empty repo), an empty list is returned gracefully
- No breaking changes to existing git_status response structure

## Verification

```
$ ruff check src/node_agent/executor.py src/hub/tools/git_operations.py
All checks passed!

$ uv run python -c "import ast; ast.parse(open('src/node_agent/executor.py').read()); ast.parse(open('src/hub/tools/git_operations.py').read()); print('Syntax valid')"
Syntax valid
```

Both ruff linting and Python syntax validation passed successfully.
