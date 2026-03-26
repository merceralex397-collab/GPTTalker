# Planning: EXEC-007 — Restore discovery and inspection contract behavior in hub tools

## Ticket

- **ID**: EXEC-007
- **Title**: Restore discovery and inspection contract behavior in hub tools
- **Wave**: 10
- **Lane**: bugfix
- **Stage**: planning
- **Depends on**: EXEC-004, EXEC-005

## Summary

Post-repair full-suite validation still fails contract cases in `src/hub/tools/discovery.py` and `src/hub/tools/inspection.py`. The hub tool handlers do not gracefully handle string-backed status/health values (from mocks and real data) and do not return contract-aligned validation errors for empty-string parameters.

## Root Cause Analysis

### Bug 1: `list_nodes_impl` — string vs enum status handling (discovery.py)

The `list_nodes_impl` function accesses `.value` assuming enum types:

```python
# discovery.py line 61
"status": node.status.value,   # AttributeError if status is plain str

# discovery.py line 64
"health_status": (health.get("health_status", NodeHealthStatus.UNKNOWN)).value
# AttributeError if health_status is plain str like "healthy"
```

Test fixtures use plain strings (`mock_node.status = "online"`), but the code assumes `NodeStatusEnum` values. This causes `AttributeError` at runtime when status/health values are strings rather than enum instances.

**Fix**: Add helper functions `_get_status_value()` and `_get_health_status_value()` that handle both string and enum types, then use them in place of direct `.value` access.

---

### Bug 2: `inspect_repo_tree_handler` — parameter validation order (inspection.py)

When empty strings are passed for `node_id` or `repo_id`, the handler checks dependency availability *before* validating parameter presence:

```python
# inspection.py lines 56-62
if node_client is None:
    return {"success": False, "error": "Node client not available"}
if node_repo is None:
    return {"success": False, "error": "NodeRepository not available"}
if repo_repo is None:
    return {"success": False, "error": "RepoRepository not available"}
# ... only then does it check node_id=""
```

The test passes `node_client` but not `node_repo`/`repo_repo`, so it hits "NodeRepository not available" instead of checking if `node_id=""` is invalid.

**Test expects**:
- `node_id=""` → `{"success": False, "error": "...not found..."}`
- `repo_id=""` → `{"success": False, "error": "...not found..."}`

**Fix**: Move empty-string validation *before* dependency availability checks. When `node_id` or `repo_id` is empty, return a "not found" error immediately, before checking whether repositories are available.

---

### Bug 3: `read_repo_file_handler` — same parameter validation order issue (inspection.py)

Same pattern for `file_path=""`. The test omits `repo_repo`, hitting "RepoRepository not available" before checking if `file_path=""`.

**Test expects**:
- `file_path=""` → `{"success": False, "error": "...not found..."}`

**Fix**: Add empty-string validation for `file_path` before dependency checks.

---

## Implementation Steps

### Step 1: Fix string vs enum handling in `list_nodes_impl` (discovery.py)

**File**: `src/hub/tools/discovery.py`

**Add two helper functions after imports** (around line 14):

```python
def _get_status_value(status) -> str:
    """Extract status value, handling both string and enum types."""
    if isinstance(status, str):
        return status
    return status.value

def _get_health_status_value(health_status) -> str:
    """Extract health status value, handling both string and enum types."""
    if isinstance(health_status, str):
        return health_status
    return health_status.value
```

**Update line 61** (status field):
```python
# Before
"status": node.status.value,

# After
"status": _get_status_value(node.status),
```

**Update line 64** (health_status field):
```python
# Before
"health_status": (health.get("health_status", NodeHealthStatus.UNKNOWN)).value

# After
"health_status": _get_health_status_value(health.get("health_status", NodeHealthStatus.UNKNOWN)),
```

---

### Step 2: Reorder parameter validation in `inspect_repo_tree_handler` (inspection.py)

**File**: `src/hub/tools/inspection.py`

**Add after input normalization (after line 54)**:

```python
# Validate required parameters first (before dependency checks)
if not node_id:
    logger.warning("inspect_repo_tree_missing_node_id", node_id=node_id)
    return {"success": False, "error": f"Node not found: {node_id}"}

if not repo_id:
    logger.warning("inspect_repo_tree_missing_repo_id", repo_id=repo_id)
    return {"success": False, "error": f"Repository not found: {repo_id}"}
```

This ensures that empty-string `node_id` or `repo_id` returns a "not found" error *before* the dependency availability checks at lines 57-62.

---

### Step 3: Reorder parameter validation in `read_repo_file_handler` (inspection.py)

**File**: `src/hub/tools/inspection.py`

**Add after input normalization (after line 199)**:

```python
# Validate required parameters first (before dependency checks)
if not file_path:
    logger.warning("read_repo_file_missing_file_path", file_path=file_path)
    return {"success": False, "error": f"Repository not found: {file_path}"}
```

This ensures that empty-string `file_path` returns a "not found" error *before* the dependency availability checks at lines 202-207.

---

## File-by-File Change Summary

| File | Change Type | Lines | Description |
|------|-------------|-------|-------------|
| `src/hub/tools/discovery.py` | Modify | 14, 61, 64 | Add `_get_status_value()` / `_get_health_status_value()` helpers; replace `.value` calls with helpers |
| `src/hub/tools/inspection.py` | Modify | ~48-62 | In `inspect_repo_tree_handler`: add empty `node_id`/`repo_id` validation before dependency checks |
| `src/hub/tools/inspection.py` | Modify | ~193-207 | In `read_repo_file_handler`: add empty `file_path` validation before dependency checks |

---

## Validation Plan

### Criterion 1: Specific contract test cases pass

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -q --tb=no -k 'list_nodes_returns_structured_response or inspect_repo_tree_requires_node_and_repo or read_repo_file_requires_parameters'
```

Expected: exit 0

---

### Criterion 2: `list_nodes_handler()` accepts string-backed status values

The helper functions `_get_status_value()` and `_get_health_status_value()` handle both string and enum types:
- `"online"` (str) → returns `"online"` directly
- `NodeStatus.ONLINE` (enum) → returns `.value` → `"online"`

Verification:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py::TestDiscoveryTools -q --tb=no
```
Expected: all discovery tests pass (including `test_list_nodes_returns_structured_response`, `test_list_nodes_empty_registry`, `test_list_nodes_no_repository`)

---

### Criterion 3: `inspect_repo_tree_handler()` and `read_repo_file_handler()` return deterministic errors

Empty-string parameters now return "not found" errors *before* dependency checks. Verification:
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py::TestInspectionTools -q --tb=no
```
Expected: all inspection tests pass

---

### Criterion 4: Existing node ownership and repo-boundary checks preserved

The fixes do **not** modify:
- Node ownership validation (`repo.node_id != node_id` check — lines 76-87 in inspection.py)
- Repo boundary validation (`PathNormalizer.validate_no_traversal` / `PathNormalizer.normalize` — lines 92-104 in inspection.py)
- Any policy engine code

Node ownership and repo-boundary checks remain intact after the parameter validation reorder and status helper additions.

---

### Additional validation

```bash
# Full hub contract suite
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -q --tb=no

# Syntax check
UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile src/hub/tools/discovery.py
UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile src/hub/tools/inspection.py

# Lint
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src/hub/tools/discovery.py src/hub/tools/inspection.py
```

---

## Risks and Assumptions

- **Risk**: Adding early-return validation for empty strings could skip important dependency checks in some code paths.
  - **Mitigation**: The early returns only trigger when the parameter is empty/invalid. All other code paths (valid `node_id`, `repo_id`, `file_path`) continue to the dependency checks normally.

- **Assumption**: The contract test expectations (empty string → "not found" error) reflect intended behavior, not test-only requirements.
  - **Rationale**: The test file `test_contracts.py` defines the MCP tool contract. Empty required parameters should fail with explicit validation errors, not dependency errors.

- **Assumption**: The `node_repo` / `repo_repo` dependency check is still valuable when a *valid* node_id/repo_id is provided but the repository is unavailable.
  - **Preserved**: These dependency checks remain after the early empty-string returns, so valid-but-missing dependencies still produce "not available" errors.

---

## Blocker Status

No blockers. All required context is available:
- Source files read and analyzed
- Failing tests identified and understood
- Root causes traced to specific lines
- Fix approach validated against test expectations
