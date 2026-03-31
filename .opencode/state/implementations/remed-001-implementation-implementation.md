# Implementation: REMED-001 — Restore Runtime-Safe Imports

## Ticket
- **ID:** REMED-001
- **Title:** One or more Python packages fail to import — the service cannot start
- **Wave:** 12
- **Lane:** runtime
- **Stage:** implementation

## Root Causes Addressed

### RC-1: FastAPI DI Anti-Pattern in `mcp.py`

**Problem:** `src/hub/mcp.py` lines 50–53 called `await get_policy_engine()` directly outside FastAPI's dependency injection context. Since `get_policy_engine()` uses `Depends()` wrappers internally that require `request.app.state`, calling it directly raised `TypeError: missing 'request' argument` on every tool call.

**Fix:** Added an `initialize(app: FastAPI)` method to `MCPProtocolHandler` that pre-builds the `PolicyAwareToolRouter` using `app.state` directly (bypassing FastAPI DI). This is called during lifespan startup before the app accepts requests. Updated `_ensure_router()` to use the pre-built router if available, with a backward-compatible fallback.

**Changed files:**
- `src/hub/mcp.py`: Added `initialize()` method, updated `_ensure_router()`
- `src/hub/lifespan.py`: Added call to `mcp_handler.initialize(app)` during startup

### RC-2: Missing `from __future__ import annotations` in `dependencies.py`

**Problem:** `src/hub/dependencies.py` used `RelationshipService` as a return type annotation (line 837) but only imported it under `TYPE_CHECKING`. Without `from __future__ import annotations`, Python evaluated the annotation at definition time and raised `NameError: name 'RelationshipService' is not defined`.

**Fix:** Added `from __future__ import annotations` at the top of `dependencies.py`.

## Implementation Details

### `src/hub/mcp.py` — `initialize()` method

The new `initialize(app: FastAPI)` method:
1. Accesses `app.state` directly to get `db_manager`, `http_client`, `config`, `qdrant_client`, `embedding_client`
2. Builds all repositories using `db_manager`
3. Builds all policy instances (`NodePolicy`, `RepoPolicy`, `WriteTargetPolicy`, `LLMServicePolicy`)
4. Builds the `PolicyEngine` if all policies are available
5. Builds HTTP clients (`HubNodeClient`, `LLMServiceClient`) if `http_client` and `config` are available
6. Builds optional services (`IndexingPipeline`, `BundleService`, `AggregationService`, `ArchitectureService`) with graceful fallback using `try/except`
7. Constructs and stores the `PolicyAwareToolRouter` in `self._router`

This bypasses FastAPI's dependency injection entirely by directly using the state that was already populated during lifespan startup.

### `src/hub/lifespan.py` — Startup Integration

Added `await mcp_handler.initialize(app)` as Step 8 in the lifespan startup, after the tunnel manager is initialized but before the app yields to accept requests.

### `src/hub/dependencies.py` — Forward Reference Fix

Added `from __future__ import annotations` to enable PEP 563 deferred annotation evaluation, preventing the `NameError` on `RelationshipService`.

## Acceptance Criteria Results

All five acceptance criteria passed:

| # | Criterion | Command | Result |
|---|---|---|---|
| AC-1 | Hub app import | `uv run python -c "from src.hub.main import app"` | PASS |
| AC-2 | Node agent import | `uv run python -c "from src.node_agent.main import app"` | PASS |
| AC-3 | Shared imports | `uv run python -c "import src.shared.models; import src.shared.schemas"` | PASS |
| AC-4 | Runtime annotations | Code inspection of modified files — no TYPE_CHECKING-only names in runtime code | PASS |
| AC-5 | Pytest collection | `uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py tests/node_agent/test_executor.py --collect-only -q` | PASS — 67 tests collected |

## Raw Command Output

```
$ uv run python -c "from src.hub.main import app; print('hub import OK')"
hub import OK

$ uv run python -c "from src.node_agent.main import app; print('node_agent import OK')"
node_agent import OK

$ uv run python -c "import src.shared.models; import src.shared.schemas; print('shared import OK')"
shared import OK

$ uv run python -c "from src.hub.tools import register_all_tools; print('tools import OK')"
tools import OK

$ uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py tests/node_agent/test_executor.py --collect-only -q
67 tests collected in 0.69s
```

## Files Modified

| File | Change |
|---|---|
| `src/hub/mcp.py` | Added `initialize()` method to pre-build router via `app.state`; updated `_ensure_router()` to use pre-built router |
| `src/hub/lifespan.py` | Added `await mcp_handler.initialize(app)` during startup (Step 8) |
| `src/hub/dependencies.py` | Added `from __future__ import annotations` to fix `RelationshipService` forward reference |

## Security Boundaries Preserved

- The fix does not widen trust boundaries
- All policy engine validations remain in place
- The router still uses `PolicyEngine` with all four policies
- Optional services that fail during initialization gracefully degrade to `None`
- No bypass of path validation, extension allowlists, or write target policies
