# Implementation of FIX-026: Fix missing node health hydration at startup causing policy denials

## Summary

Added Step 8b in `src/hub/lifespan.py` after `mcp_handler.initialize()` and before `yield` to hydrate node health for all registered nodes before the hub accepts traffic. The implementation uses a fail-open try/except pattern matching the existing Qdrant startup pattern (lines 79-96 in lifespan.py).

## Changes Made

**File: `src/hub/lifespan.py`**

Added after line 140 (`logger.info("mcp_handler_initialized")`):

```python
    # Step 8b: Hydrate node health for all registered nodes before accepting traffic
    # (fail-open: log warning but continue if health check fails)
    try:
        from src.hub.services.node_health import NodeHealthService

        node_health_service = NodeHealthService(
            http_client=app.state.http_client,
            node_repo=app.state.db_manager._repos.node,
            auth_handler=None,
        )
        await node_health_service.check_all_nodes()
        logger.info("node_health_hydrated")
    except Exception as e:
        logger.warning(
            "node_health_hydration_failed_continuing",
            error=str(e),
            exc_info=e,
        )
```

## Validation

Command:
```bash
uv run .venv/bin/python -c "from src.hub.lifespan import lifespan; print('OK')"
```

Raw Command Output:
```
OK
```

Result: PASS

## Implementation Notes

- Only `src/hub/lifespan.py` was modified (no other files)
- Fail-open pattern matches existing Qdrant startup pattern at lines 79-96
- If `check_all_nodes()` raises an exception, it logs a warning and continues (hub does not crash)
- NodeHealthService is constructed with `http_client`, `node_repo`, and `auth_handler=None` (consistent with FIX-025 wiring)
- The `node_repo` is accessed via `app.state.db_manager._repos.node` (same pattern used elsewhere in the codebase)
