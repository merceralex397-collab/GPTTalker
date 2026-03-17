# QA Verification: REPO-003

## Ticket
- **ID**: REPO-003
- **Title**: search_repo and git_status tools
- **Stage**: qa
- **Status**: qa

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Search uses bounded ripgrep execution | **PASSED** |
| 2 | Git status is exposed read-only | **PASSED** |
| 3 | Timeout and error handling are explicit | **PASSED** |

## Verification Details

### Criterion 1: Bounded ripgrep execution

**Implementation Files:**
- `src/hub/tools/search.py` - Hub-side handler with path validation
- `src/node_agent/executor.py` - Node-side ripgrep execution
- `src/node_agent/routes/operations.py` - HTTP endpoint

**Evidence:**
1. **Hub path validation** (`search.py` lines 107-121):
   - Uses `PathNormalizer.validate_no_traversal(path)` to prevent traversal attacks
   - Uses `PathNormalizer.normalize(path, repo_path)` to scope path to repo root

2. **Node path validation** (`executor.py` lines 173-174):
   - Uses `_validate_path()` which resolves path and checks against `allowed_paths`
   - Raises `PermissionError` if path is outside allowed boundaries

3. **Bounded ripgrep execution** (`executor.py` lines 181-215):
   - Uses `shutil.which("rg")` to verify ripgrep is available
   - Builds command with `--line-number`, `--no-heading`, `--hidden`, `-c` flags
   - Supports `--glob` for file pattern filtering
   - Executes via `asyncio.create_subprocess_exec()` with explicit timeout
   - Handles `TimeoutError` with message: "Search timed out after {timeout} seconds"

**Verdict**: PASSED - Both hub and node layers validate paths; ripgrep execution is bounded with timeout.

---

### Criterion 2: Read-only git

**Implementation Files:**
- `src/hub/tools/git_operations.py` - Hub-side handler
- `src/node_agent/executor.py` - Node-side git operations

**Evidence:**
1. **Explicit documentation** (`git_operations.py` lines 33-36):
   ```
   This tool only exposes read-only git operations:
   - git status --porcelain (clean/modified/staged/untracked)
   - git branch --show-current (current branch)
   - git rev-list (ahead/behind count relative to remote)
   ```

2. **Read-only commands** (`executor.py` lines 318-390):
   - Line 318: `git branch --show-current`
   - Line 322: `git rev-parse --short HEAD`
   - Line 326: `git status --porcelain`
   - Lines 362-367: `git rev-list --left-right --count`

3. **No write operations**: No `git add`, `git commit`, `git push`, `git pull`, `git merge`, etc.

**Verdict**: PASSED - Only read-only git commands are exposed.

---

### Criterion 3: Timeout and error handling are explicit

**Implementation Files:**
- `src/hub/tools/search.py` - Search handler
- `src/hub/tools/git_operations.py` - Git status handler
- `src/node_agent/executor.py` - Execution layer
- `src/node_agent/routes/operations.py` - HTTP endpoints

**Evidence:**
1. **Timeout validation**:
   - `search.py` (lines 66-69): Caps timeout to 1-120 seconds
   - `git_operations.py` (lines 52-55): Caps timeout to 1-60 seconds
   - `operations.py` (lines 208-212): Validates search timeout 1-120 seconds
   - `operations.py` (lines 272-276): Validates git timeout 1-60 seconds

2. **Timeout handling**:
   - `executor.py` (lines 205-210): `TimeoutError` caught, process killed, error raised
   - `executor.py` (lines 306-310): `TimeoutError` caught, process killed, error raised

3. **Error handling**:
   - `executor.py` (lines 212-215): Non-zero return code handling with stderr parsing
   - `executor.py` (lines 327-328): Git status error handling
   - All handlers return `{"success": False, "error": "..."}` structure

4. **Logging**: All operations include structured logging with trace_id, duration, and outcome

**Verdict**: PASSED - Explicit timeout bounds, proper TimeoutError handling, structured error responses.

---

## Validation Commands

```bash
# Lint check
ruff check src/hub/tools/search.py src/hub/tools/git_operations.py src/node_agent/executor.py

# Type check (if configured)
python -m py_compile src/hub/tools/search.py src/hub/tools/git_operations.py src/node_agent/executor.py
```

## QA Decision

**STATUS: PASSED**

All 3 acceptance criteria verified through code inspection:
- Bounded ripgrep execution with path validation at hub and node layers
- Read-only git operations (only status, branch, rev-list)
- Explicit timeout handling with proper error responses

**Runtime validation**: Skipped due to bash permission restriction in environment.

**Closeout readiness**: Ready to advance to closeout.
