# FIX-028 Planning: Fix NodeHealthService construction using wrong db_manager reference

## Root Cause
In `src/hub/lifespan.py` lines 147-150, `NodeHealthService` is constructed with:
```python
node_health_service = NodeHealthService(
    http_client=app.state.http_client,
    node_repo=app.state.db_manager._repos.node,  # BUG: DatabaseManager has no _repos attribute
    auth_handler=None,
)
```

`DatabaseManager` in `src/shared/database.py` has no `_repos` attribute. This causes `AttributeError` when the health service tries to persist health status, resulting in:
- `health_status=unknown` for all registered nodes
- `health_check_count=0` (never updated)

## Correct Pattern
The correct wiring already exists in two places:

**`src/hub/dependencies.py` (lines 178-183):**
```python
auth_handler = NodeAuthHandler(config.node_client_api_key)
return NodeHealthService(
    node_repo=node_repo,
    http_client=http_client,
    auth_handler=auth_handler,
)
```

**`src/hub/mcp.py` (lines 91-96):**
```python
node_health_service = (
    NodeHealthService(
        node_repo=node_repo,
        http_client=http_client,
        auth_handler=auth_handler,
    )
)
```

## Implementation
Single-file change in `src/hub/lifespan.py`:

1. Import `NodeRepository` from `src.hub.repositories.nodes`
2. Import `NodeAuthHandler` from `src.hub.services.node_health`
3. Construct `NodeRepository(app.state.db_manager)` properly
4. Construct `NodeAuthHandler(config.node_client_api_key)` properly
5. Pass both to `NodeHealthService(...)` instead of `app.state.db_manager._repos.node` and `None`

## Files to Modify
- `src/hub/lifespan.py` (lines 144-151)

## Acceptance Criteria
1. `lifespan.py` constructs `NodeHealthService` using `NodeRepository(db_manager) + NodeAuthHandler(config.node_client_api_key)` — same pattern as dependencies.py and mcp.py
2. After fix, `list_nodes` reports `health_status!=unknown` for reachable registered nodes
3. Node-scoped MCP tools no longer fail with `unknown_health_status` policy denial
4. `UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.lifespan import lifespan; print("OK")'` exits 0
5. After hub restart, `health_check_count > 0` for registered nodes

## Validation Plan
1. Import check: `python -c 'from src.hub.lifespan import lifespan; print("OK")'` exits 0
2. Code inspection confirms correct wiring pattern
3. Run `uv run python -c "from src.hub.lifespan import lifespan; print('OK')"` to verify fix
