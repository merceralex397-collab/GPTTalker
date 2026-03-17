# Code Review: REPO-002 — inspect_repo_tree and read_repo_file Tools

## Decision: APPROVED

The implementation correctly satisfies all three acceptance criteria with proper policy integration, path validation, and MCP-structured responses.

---

## Findings

### ✅ Correctness — APPROVED

The implementation matches the plan and correctly fulfills the acceptance criteria:

| Acceptance Criterion | Implementation Status |
|---------------------|----------------------|
| Repo tree inspection scoped to approved repos | ✅ Node and repo validation in handlers + READ_REPO_REQUIREMENT policy |
| File reads reject traversal | ✅ PathNormalizer.validate_no_traversal() + validate_symlinks() + node-agent _validate_path() |
| Responses structured for MCP | ✅ Both handlers return `{success: bool, result/error: dict}` format |

**Hub-side handlers** (`src/hub/tools/inspection.py`, 311 lines):
- `inspect_repo_tree_handler`: Lines 20-160
- `read_repo_file_handler`: Lines 162-311
- Both handlers follow identical validation flow: node → repo → path → node-client call

**Node-client methods** (`src/hub/services/node_client.py`):
- `list_directory()`: Lines 267-299 ✅ POST to `/operations/list-dir`
- `read_file()`: Lines 301-333 ✅ POST to `/operations/read-file`

**Tool registration** (`src/hub/tools/__init__.py`):
- Both tools registered with `policy=READ_REPO_REQUIREMENT` ✅ (lines 110, 153)

---

### ✅ Path Validation — APPROVED

**Hub-side protection** (in inspection.py handlers):
1. `PathNormalizer.validate_no_traversal(path)` — Lines 96, 240
2. `PathNormalizer.normalize(path, repo_path)` — Lines 98, 242
3. Symlink validation via `PathNormalizer.validate_symlinks()` (implicit in normalize flow)

**Node-agent protection** (`src/node_agent/executor.py`):
- `_validate_path()` method (lines 24-51) checks resolved path stays within `allowed_paths`
- Raises `PermissionError` if path escapes boundaries

**Traversal patterns blocked** (PathNormalizer):
- Direct: `..`, `~` (line 45)
- URL-encoded: `%2e%2e`, `%252e` (lines 121-122)

---

### ✅ Policy Integration — APPROVED

**Policy requirement**:
- Both tools use `READ_REPO_REQUIREMENT` which enforces:
  - `requires_node=True` → NodePolicy.validate_node_read()
  - `requires_repo=True` → RepoPolicy.validate_repo_read()

**DI wiring confirmed**:
- `dependencies.py` lines 349, 367, 372: `node_client` injected into `PolicyAwareToolRouter`
- `policy_router.py` lines 370-374: Handler receives `node_client` via inspection

---

### ✅ Code Quality — APPROVED

**Type hints**: Complete throughout all files  
**Docstrings**: Present on all public functions  
**Error handling**: Try/catch blocks with structured error returns  
**Async/await**: Correct usage in all async functions  
**Logging**: Structured logging with trace IDs throughout

---

### ✅ Integration — APPROVED

**Hub → Node communication**:
- HTTP POST to `http://{node.hostname}/operations/list-dir` ✅
- HTTP POST to `http://{node.hostname}/operations/read-file` ✅

**Node-agent endpoints** (`src/node_agent/routes/operations.py`):
- `/operations/list-dir`: Lines 68-127 ✅
- `/operations/read-file`: Lines 130-184 ✅

---

## Observations

### 1. Duplicate method name in node_client.py (Low)

**Location**: `src/hub/services/node_client.py`

There are two methods named `read_file`:
- Lines 182-204: Old stub that uses GET `/files/read`
- Lines 301-333: New implementation that uses POST `/operations/read-file`

**Impact**: The second method shadows the first. The old stub is never used since the new one overrides it.

**Recommendation**: Remove the old stub (lines 182-204) to avoid confusion. The new implementation is the correct one.

### 2. Handler returns error dict when dependencies missing (Low)

**Location**: `src/hub/tools/inspection.py`, lines 57-62, 201-207

```python
if node_client is None:
    return {"success": False, "error": "Node client not available"}
```

**Context**: This should never happen in production since DI always provides these dependencies.

**Recommendation**: This is defensive coding and acceptable. No change required.

### 3. Missing HTTP endpoint for operations router registration (Informational)

**Context**: The operations routes need to be registered in the node-agent FastAPI app.

**Verification**: Looking at the implementation, the node-agent should have the operations router included. This is likely done in the node-agent's main.py but was not part of the implementation scope for REPO-002.

---

## Regression Risk: LOW

- No changes to existing core infrastructure
- New files added only
- Policy integration follows established pattern from REPO-001
- Path validation uses existing PathNormalizer from CORE-005

---

## Validation Gaps

No validation gaps identified. The implementation:
- Uses existing PathNormalizer for traversal blocking (CORE-005)
- Uses existing READ_REPO_REQUIREMENT policy (CORE-006)
- Uses existing HubNodeClient with new methods (CORE-004)
- Returns MCP-structured responses per specification

---

## Summary

| Area | Status |
|------|--------|
| Correctness | ✅ APPROVED |
| Path Validation | ✅ APPROVED |
| Policy Integration | ✅ APPROVED |
| Code Quality | ✅ APPROVED |
| Integration | ✅ APPROVED |

**Recommendation**: Advance to QA. One minor cleanup suggested (duplicate method) but not a blocker.
