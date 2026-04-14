---
kind: plan
stage: planning
ticket_id: REMED-015
---

# REMED-015 Planning

## Ticket
- ID: REMED-015
- Title: Remediation review artifact does not contain runnable command evidence
- Wave: 34
- Lane: remediation
- Source ticket: REMED-007
- Finding source: EXEC-REMED-001

## Affected surfaces
- `tickets/manifest.json`
- `.opencode/state/reviews/remed-004-review-ticket-reconciliation.md`

## Finding analysis

The validated finding `EXEC-REMED-001` was originally about Python import failures in node-agent FastAPI dependency injection. Through the prior remediation chain (REMED-001, REMED-002, REMED-008, REMED-011, REMED-012, REMED-013, REMED-014), all production fixes have been confirmed present in the current codebase:

1. **FastAPI DI pattern** (`request: Request`, not `app: FastAPI`) — confirmed present in `src/node_agent/dependencies.py`
2. **TYPE_CHECKING forward reference hygiene** (`from __future__ import annotations`) — confirmed present in `src/hub/dependencies.py` and `src/shared/models.py`
3. **MCP initialize() method** (bypasses DI anti-pattern via lifespan) — confirmed present in `src/hub/mcp.py`
4. **NodeHealthService wiring** (NodeRepository(db_manager) + NodeAuthHandler) — confirmed present in `src/hub/lifespan.py` and `src/hub/mcp.py`
5. **Auth enforcement on node-agent routes** (require_api_key dependency) — confirmed present in `src/node_agent/routes/operations.py`
6. **Response envelope handling** (no double-wrapping) — confirmed present in `src/hub/transport/mcp.py`
7. **Path-mode search parsing** (--files-with-matches correctly parsed) — confirmed present in `src/node_agent/executor.py`

The finding is **STALE** — no code changes required. All remediation chain fixes are already in place.

## Acceptance criteria
1. The validated finding `EXEC-REMED-001` no longer reproduces.
2. Current quality checks rerun with evidence tied to the fix approach.

## Approach
- No code changes needed (finding is stale)
- QA section will include 3 import verification commands using `UV_CACHE_DIR=/tmp/uv-cache uv run python -c '...'` format
- All 3 commands expected to exit 0 with OK output

## Verification commands
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.node_agent.main import app; print("OK")'
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.mcp import MCPProtocolHandler; print("OK")'
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.node_agent.dependencies import get_config, get_executor; print("OK")'
```

All expected to exit 0.