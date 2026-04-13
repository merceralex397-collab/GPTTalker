# FIX-026 Planning Artifact

## Ticket
- **ID:** FIX-026
- **Title:** Fix missing node health hydration at startup causing policy denials
- **Wave:** 23
- **Lane:** bugfix
- **Stage:** planning
- **Kind:** plan

---

## Root Cause Analysis

The bug is confirmed by tracing the code path from startup through to policy enforcement:

### Step 1: Registration leaves health columns NULL
When a node is registered via `NodeRepository.create()`, the health columns (`health_status`, `last_health_check`, `latency_ms`) are set to `NULL` in the database. The `NodeHealth.__init__()` defaults to `NodeHealthStatus.UNKNOWN`.

### Step 2: FIX-025 wired NodeHealthService correctly
`MCPProtocolHandler.initialize()` (mcp.py:91-99) now constructs `NodeHealthService` with real dependencies instead of passing `None`. This fixed the prior crash ("'NoneType' object has no attribute 'get_node_health'").

### Step 3: `check_all_nodes()` is never called at startup
`NodeHealthService.check_all_nodes()` (node_health.py:247-260) iterates all registered nodes, calls `check_node_health()` for each, and persists results via `NodeRepository.update_health()`. **This method is never invoked during hub startup.**

### Step 4: Policy enforcement sees UNKNOWN health
`NodePolicy.validate_node_access()` (node_policy.py:88) calls:
```python
health = await self._health.get_node_health(node_id)
```
This returns a `NodeHealth` with `health_status=NodeHealthStatus.UNKNOWN` (the default when DB columns are NULL). The policy then rejects at node_policy.py:110:
```python
if health_status == NodeHealthStatus.UNKNOWN:
    ...
    return NodeAccessResult(approved=False, ..., rejection_reason="unknown_health_status")
```

### Visual call chain at startup
```
lifespan()
  └─> mcp_handler.initialize(app)   [Step 8 - builds router with NodePolicy]
                                          │
                                          ▼
                               NodePolicy(node_repo, node_health_service)
                                          │
                                          ▼
                               [NO call to check_all_nodes()] ← MISSING
```

### Missing call chain (what needs to happen)
```
lifespan()
  └─> mcp_handler.initialize(app)   [Step 8 - builds router]
  └─> node_health_service.check_all_nodes()   [NEW Step 8b - hydrate health]
           │
           └─> NodeRepository.list_all() → gets all nodes
           └─> for each node: check_node_health() → hits node /health endpoint
           └─> NodeRepository.update_health() → persists HEALTHY to DB
```

---

## File-by-File Changes

### File 1: `src/hub/lifespan.py`
**Change:** Add a new Step 8b between Step 8 (mcp_handler.initialize) and the yield.

**Location:** After line 140 (`logger.info("mcp_handler_initialized")`), before line 142 (`yield`).

**New code:**
```python
# Step 8b: Hydrate node health status for all registered nodes
# This must happen after MCP router is built but before the hub accepts traffic.
# Uses fail-open pattern: log error but don't crash hub startup.
try:
    from src.hub.services.node_health import NodeHealthService
    from src.hub.services.auth import NodeAuthHandler
    from src.shared.repositories.nodes import NodeRepository

    node_repo = NodeRepository(app.state.db_manager)
    auth_handler = NodeAuthHandler(app.state.config.node_client_api_key)
    health_service = NodeHealthService(
        node_repo=node_repo,
        http_client=app.state.http_client,
        auth_handler=auth_handler,
    )

    results = await health_service.check_all_nodes()
    healthy_count = sum(1 for r in results if r.health_status.value == "healthy")
    logger.info(
        "node_health_hydration_complete",
        total_nodes=len(results),
        healthy_count=healthy_count,
    )
except Exception as e:
    # Fail-open: log error but allow hub to start
    logger.error(
        "node_health_hydration_failed_continuing",
        error=str(e),
    )
```

**Rationale:**
- Uses `fail-open` pattern consistent with existing Qdrant initialization (lifespan.py:88-96)
- Creates `NodeHealthService` with same dependencies as `mcp.py:91-99` — the service is already correctly wired after FIX-025
- `check_all_nodes()` is the correct method: it hits each node's `/health` endpoint and persists the result to DB via `update_health()`
- Error is logged but hub continues starting

---

## Implementation Steps

1. **Read current lifespan.py** to confirm Step 8 placement (line 139-141)
2. **Add import block** for `NodeHealthService`, `NodeAuthHandler`, and `NodeRepository` inside the try block
3. **Construct `NodeHealthService`** using `app.state.db_manager`, `app.state.http_client`, and `app.state.config.node_client_api_key`
4. **Call `health_service.check_all_nodes()`** and log summary
5. **Wrap in try/except** with fail-open logging (consistent with Qdrant pattern)
6. **Verify the placement** is after `mcp_handler.initialize()` and before `yield`

---

## Validation Plan

### Acceptance Criteria Mapping

| # | Acceptance Criterion | Verification Method |
|---|---------------------|---------------------|
| 1 | After hub+node restart, list_repos succeeds or returns domain errors | Runtime test after full restart |
| 2 | After hub+node restart, git_status succeeds or returns domain errors | Runtime test after full restart |
| 3 | After hub+node restart, inspect_repo_tree succeeds or returns domain errors | Runtime test after full restart |
| 4 | Node health hydrated to HEALTHY before NodePolicy enforcement | Code inspection: check_all_nodes() called before yield |
| 5 | `python -c 'from src.hub.mcp import MCPProtocolHandler; from src.hub.lifespan import lifespan; print("OK")'` exits 0 | Smoke test: import validation |
| 6 | If check_all_nodes() raises, hub logs error but doesn't crash | Code inspection: try/except with fail-open pattern |
| 7 | list_nodes continues to work | list_nodes doesn't use NodePolicy.validate_node_access() directly |

### Code Inspection Checklist
- [ ] `check_all_nodes()` is called after `mcp_handler.initialize()` in lifespan
- [ ] `NodeHealthService` is constructed with correct dependencies (node_repo, http_client, auth_handler)
- [ ] `try/except` wraps the call with fail-open logging
- [ ] `logger.error` is used for the failure case (not `warning`) so it's visible
- [ ] No changes to `node_policy.py`, `node_client.py`, or tool handlers
- [ ] Import test (acceptance criterion 5) exits 0

### Smoke Test
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.lifespan import lifespan; from src.hub.mcp import MCPProtocolHandler; print("OK")'
```

---

## No Changes Required To

| File | Reason |
|------|--------|
| `src/hub/policy/node_policy.py` | Policy logic is correct; UNKNOWN→reject is correct fail-closed behavior |
| `src/hub/services/node_health.py` | `check_all_nodes()` method already exists and works correctly |
| `src/hub/mcp.py` | NodeHealthService wiring was fixed in FIX-025; no further changes needed |
| `src/shared/repositories/nodes.py` | `update_health()` method already exists |
| Tool handlers (inspection.py, search.py, git_operations.py) | The symptom was policy rejection; fix is upstream at startup |

---

## Risks and Assumptions

### Risks
1. **Node unreachable at startup:** If a node is offline when `check_all_nodes()` runs at startup, its health will be set to OFFLINE/UNHEALTHY and `NodePolicy.validate_node_access()` will still reject it. This is correct behavior — nodes must be reachable to be used.
2. **Startup time increase:** `check_all_nodes()` makes HTTP requests to all registered nodes. For large node counts, this adds latency to startup. However, this is the same latency that would occur on first use anyway.

### Assumptions
1. Nodes are registered and have `node_id` and `hostname` set correctly in the DB
2. The node's `/health` endpoint is accessible over the tailnet
3. `NodeRepository.update_health()` correctly persists health columns to the `nodes` table

---

## Blockers

**None.** All required dependencies are in place:
- `NodeHealthService.check_all_nodes()` exists and is correct
- `NodeRepository.update_health()` exists and persists correctly
- The service is already wired in `mcp.py` (FIX-025)
- The only missing piece is the **call** at startup
