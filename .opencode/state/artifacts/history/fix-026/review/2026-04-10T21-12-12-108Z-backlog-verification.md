# Backlog Verification: FIX-026

## Ticket

| Field | Value |
|---|---|
| ID | FIX-026 |
| Title | Fix missing node health hydration at startup causing policy denials |
| Stage | closeout |
| Status | done |
| Resolution | done |
| Verification | trusted |

## Finding Source

FIX-026 was a net-new-scope ticket (not from post-completion defect) that identified the missing `check_all_nodes()` call at startup.

## Original Problem

`check_all_nodes()` was never called at hub startup, so nodes remained with `health_status=unknown` until their first on-demand health poll. Node-scoped MCP tools would fail with `Policy violation: Node access denied: unknown_health_status` until health was hydrated.

## Fix Applied

Added Step 8b in `src/hub/lifespan.py` to call `node_health_service.check_all_nodes()` after MCP initialization, using a fail-open try/except pattern:
```python
try:
    node_health_service.check_all_nodes()
except Exception as e:
    logger.error(f"Failed to hydrate node health at startup: {e}")
```

## Verification Evidence

### Live Runtime Confirmation

1. **Database health check**: `localnode` has `health_status = "healthy"` and `health_check_count > 0` in the SQLite database (`data/gpttalker.db`)
2. **MCP tool success**: All node-scoped MCP probes succeed without `unknown_health_status` policy denials
3. **Node registration**: `localnode` is registered in the database, confirming the startup hydration found nodes to hydrate

### Source Code Verification

The fixed code in `src/hub/lifespan.py` (lines ~145-156) shows:
- `check_all_nodes()` is called after MCP handler initialization
- The call is wrapped in a fail-open try/except so startup failures don't crash the hub
- If no nodes are registered, the call gracefully no-ops

## Result

**PASS** — All acceptance criteria verified via live runtime and source code inspection. Node health is hydrated at startup. No regression. No follow-up required.