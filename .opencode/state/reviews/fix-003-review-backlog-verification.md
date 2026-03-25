# Backlog Verification — FIX-003

## Ticket
- **ID:** FIX-003
- **Title:** Fix hub MCP router async wiring and circular import
- **Stage:** closeout
- **Status:** done
- **Verification state:** PASS

## Verification Summary
All three issues in this ticket were verified fixed:
1. Circular import between `main.py` and `routes.py` — resolved via `handlers.py` intermediate layer
2. `_ensure_router()` async wiring — method is now properly async with `await`
3. Duplicate `/health` endpoints — single `/health` endpoint remains in `routes.py`

## Evidence
1. **Import verification:** `from src.hub.main import app` succeeds — no circular import
2. **Routing verification:** `PolicyAwareToolRouter` methods properly await `_ensure_router()`
3. **Endpoint verification:** Single `/health` in routes.py; health check in main.py removed

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| MCP endpoints respond correctly in async FastAPI context | PASS |
| No circular import between main.py and routes.py | PASS |
| Single /health endpoint definition | PASS |
| `python3 -c 'from src.hub.main import app'` succeeds | PASS |

## Notes
- This fix was a prerequisite for all subsequent EXEC tickets
- The `handlers.py` intermediate layer cleanly breaks the circular dependency
- No follow-up ticket needed
