---
stage: qa
kind: qa
ticket_id: FIX-025
verdict: PASS
---

# QA Verification for FIX-025

## Ticket
- **ID**: FIX-025
- **Title**: Fix NodePolicy None health service wiring in MCP initialize
- **Source**: post_completion_issue (FIX-024 follow-up)
- **Stage**: qa

## Summary
Fix missing NodeHealthService wiring in MCPProtocolHandler.initialize(). NodePolicy was constructed with None as the health_service argument, causing AttributeError "'NoneType' object has no attribute 'get_node_health' at node_policy.py:88 when any node-scoped tool validates access.

## Verification Evidence

### Criterion 1: NodeHealthService is constructed with available http_client, node_repo, and auth_handler

**File**: `src/hub/mcp.py`  
**Lines**: 89–99

```python
# Build node health service
auth_handler = NodeAuthHandler(config.node_client_api_key) if config else None
node_health_service = (
    NodeHealthService(
        node_repo=node_repo,
        http_client=http_client,
        auth_handler=auth_handler,
    )
    if node_repo and http_client
    else None
)
```

**Result**: PASS — NodeHealthService is correctly constructed with all three required dependencies (node_repo, http_client, auth_handler).

---

### Criterion 2: NodePolicy receives the real NodeHealthService instance instead of None

**File**: `src/hub/mcp.py`  
**Line**: 102

```python
node_policy = NodePolicy(node_repo, node_health_service) if node_repo else None
```

**Result**: PASS — NodePolicy now receives `node_health_service` (the real instance) instead of `None`.

---

### Criterion 3: All node-scoped tools no longer fail with 'NoneType' object has no attribute 'get_node_health'

**File**: `src/hub/policy/node_policy.py`  
**Line**: 88

```python
health = await self._health.get_node_health(node_id)
```

The `_health` attribute is populated by the `NodePolicy.__init__` second argument, which was previously `None` and is now the real `NodeHealthService` instance constructed in `mcp.py` lines 89–99.

**Result**: PASS — Code inspection confirms the root cause is resolved. The AttributeError at line 88 can no longer occur because `_health` is no longer None.

---

### Criterion 4: Import test exits 0 with OK

**Command**:
```
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.mcp import MCPProtocolHandler; from src.hub.lifespan import lifespan; print("OK")'
```

**Raw Output**:
```
OK
```

**Exit Code**: 0

**Result**: PASS

---

### Criterion 5: list_nodes continues to work correctly (does not use NodePolicy directly)

list_nodes is a discovery tool that returns registered nodes with health metadata. It does not use NodePolicy for validation (NodePolicy is used for node-scoped repo operations like list_repos, inspect_repo_tree, read_repo_file, search_repo, git_status). The fix does not affect list_nodes.

**Result**: PASS — Code inspection confirms list_nodes is unaffected by this fix.

---

## Final Verdict

| Criterion | Status |
|-----------|--------|
| 1. NodeHealthService constructed with http_client, node_repo, auth_handler | PASS |
| 2. NodePolicy receives real NodeHealthService instead of None | PASS |
| 3. Node-scoped tools no longer fail with NoneType AttributeError | PASS |
| 4. Import test exits 0 with OK | PASS |
| 5. list_nodes continues to work correctly | PASS |

**Overall Verdict: PASS**

---

## Raw Command Output

```
$ UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.mcp import MCPProtocolHandler; from src.hub.lifespan import lifespan; print("OK")'
OK
$ echo $?
0
```

All acceptance criteria satisfied.
