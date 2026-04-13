# Ticket Reconciliation: FIX-027 superseded by FIX-028

## Reconciliation Summary

| Field | Value |
|---|---|
| Source Ticket (Authoritative) | FIX-028 |
| Target Ticket (Stale/Superseded) | FIX-027 |
| Supersede Target | true |
| Reason | FIX-028 already delivered the same fix that FIX-027 was planning to solve. The NodeHealthService wiring in lifespan.py (NodeRepository(db_manager) + NodeAuthHandler(config.node_client_api_key)) was correctly applied by FIX-028. Live runtime confirms localnode is healthy with health_check_count > 0. FIX-027's finding_source (FIX-026) is the same as FIX-028's, and FIX-028's fix supersedes what FIX-027 was planning to do. |

## Background

FIX-027 was opened as a post-completion issue from FIX-026 with the concern that "check_all_nodes() is called at startup but health status is not being persisted for registered nodes." The decision blockers were:

1. The fix must handle the case where no nodes are registered at startup time (graceful no-op vs. error)
2. The fix must handle auth_handler=None correctly for localnode health checks without crashing
3. Acceptance must be verified by actually calling the MCP tools against a registered node after fresh restart

However, FIX-028 was subsequently opened and identified the **actual root cause**: the `NodeHealthService` in `lifespan.py` was being constructed with a broken `db_manager` reference (`app.state.db_manager._repos.node`) instead of the correct `NodeRepository(db_manager)` pattern.

FIX-028's fix corrected the wiring to use:
```python
node_repo = NodeRepository(db_manager)
auth_handler = NodeAuthHandler(config.node_client_api_key)
node_health_service = NodeHealthService(
    http_client=http_client,
    node_repo=node_repo,
    auth_handler=auth_handler,
)
```

This same correct pattern was already being used in `dependencies.py` and `mcp.py`.

## Live Runtime Evidence

The live runtime (post-FIX-028) confirms:
- `localnode` is registered in the database
- `health_status = "healthy"` with `health_check_count > 0`
- All MCP probes (list_repos, git_status, inspect_repo_tree) succeed without `unknown_health_status` policy denials

## Conclusion

FIX-028 already solved the exact problem FIX-027 was investigating. The root cause was not "check_all_nodes() not being called" but rather "NodeHealthService constructed with wrong db_manager reference." Since FIX-028 correctly fixed this, FIX-027 is now redundant and should be closed as superseded.

## Verification

- Source ticket: FIX-028 (`resolution_state: done, verification_state: trusted`)
- Target ticket: FIX-027 (`resolution_state: open, stage: planning, status: todo`)
- Finding source for both: FIX-026
