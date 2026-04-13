# Backlog Verification: FIX-025

## Ticket

| Field | Value |
|---|---|
| ID | FIX-025 |
| Title | Fix NodePolicy None health service wiring in MCP initialize |
| Stage | closeout |
| Status | done |
| Resolution | done |
| Verification | trusted |

## Finding Source

FIX-024 (post-completion defect)

## Original Problem

FIX-024 identified that `MCPProtocolHandler.initialize()` constructed `NodePolicy` with `health_service=None`, causing `AttributeError: "'NoneType' object has no attribute 'get_node_health'"` at `node_policy.py:88` when any node-scoped tool validated access.

## Fix Applied

Fixed the two-step wiring in `src/hub/mcp.py`:
1. Construct `NodeHealthService` with `node_repo`, `http_client`, and `auth_handler`
2. Pass the real instance to `NodePolicy` instead of `None`

## Verification Evidence

### Live Runtime Confirmation

The live runtime (post-FIX-028 repair) confirms the fix is working:

1. **Database health check**: `localnode` has `health_status = "healthy"` and `health_check_count > 0` in the SQLite database (`data/gpttalker.db`)
2. **MCP tool success**: All node-scoped MCP probes succeed without `unknown_health_status` policy denials
3. **No None-type errors**: The original error signature (`'NoneType' object has no attribute 'get_node_health'`) is no longer present in runtime

### Source Code Verification

The fixed code in `src/hub/mcp.py` (lines ~91-96) shows:
- `NodeHealthService` is constructed with `NodeRepository(db_manager)`, `http_client`, and `NodeAuthHandler(config.node_client_api_key)`
- `NodePolicy` receives the real `NodeHealthService` instance
- No `None` health service is passed anywhere in the chain

### Comparison with Reference Patterns

The FIX-025 wiring matches the pattern already established in:
- `src/hub/dependencies.py` (lines 178-183) — `NodeRepository(db_manager)` + `NodeAuthHandler` construction
- `src/hub/mcp.py` — same pattern applied in FIX-025's fix

## Result

**PASS** — All acceptance criteria verified via live runtime and source code inspection. The original error signature is gone. No regression. No follow-up required.