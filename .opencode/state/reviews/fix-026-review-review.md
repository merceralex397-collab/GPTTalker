# Code Review: FIX-026

## Ticket
- **ID:** FIX-026
- **Title:** Fix missing node health hydration at startup causing policy denials
- **Stage:** review
- **Lane:** bugfix

## Verdict: PASS

## Review Checks

| Check | Result |
|---|---|
| Step 8b placed after mcp_handler.initialize() and before yield | PASS |
| NodeHealthService construction correct (http_client, node_repo, auth_handler=None) | PASS |
| Fail-open try/except pattern matches existing Qdrant pattern (lines 79-96) | PASS |
| No regressions to other startup steps | PASS |
| No security boundary changes | PASS |
| Import validation | PASS |

## Code Inspection

**File:** `src/hub/lifespan.py` (lines 142-159)

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

**Placement verification:**
- After `await mcp_handler.initialize()` (line 139) ✓
- Before `yield` (line 162) ✓

**Construction verification:**
- `http_client=app.state.http_client` — matches FIX-025 wiring ✓
- `node_repo=app.state.db_manager._repos.node` — consistent with FIX-025 pattern ✓
- `auth_handler=None` — correct, no auth needed for health polling (matches FIX-025) ✓

**Fail-open pattern verification** (matches Qdrant lines 79-96):
- `try:` block wraps the operation ✓
- `except Exception as e:` catches all exceptions ✓
- `logger.warning()` with `error=str(e)` and `exc_info=e` ✓
- No `raise` — hub continues startup ✓

**Security:** No trust boundary changes. NodeHealthService only reads health metadata; auth_handler=None is intentional for anonymous health polling.

## Command

```bash
uv run python -c 'from src.hub.lifespan import lifespan; print("OK")'
```

## Raw Command Output

```
OK
```

## Result: PASS

The import succeeds (exit 0) and outputs "OK". All 5 acceptance criteria are verifiable: criterion 1 (import exit 0) confirmed, criteria 2-5 verified by code inspection of the fail-open hydration block correctly placed in the startup sequence.
