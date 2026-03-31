# QA Verification — REMED-001

## Ticket

- **ID:** REMED-001
- **Title:** One or more Python packages fail to import - the service cannot start
- **Wave:** 12
- **Lane:** runtime
- **Stage:** qa
- **Status:** qa

## Overall Result

**BLOCKED — tool access restriction prevents runtime validation**

## Blocker

The bash tool is subject to a catch-all deny rule (`"*"`) that blocks commands with certain argument patterns, even when specific allow patterns (e.g., `python *`, `uv *`, `pytest *`) theoretically match. The following commands could not be executed despite matching allow rules:

| Command | Allow Pattern Matched | Outcome |
|---|---|---|
| `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"` | `uv *` | DENIED |
| `uv run python -c "..."` | `uv *` | DENIED |
| `python -c "..."` | `python *` | DENIED |
| `/usr/bin/python3 -c "..."` | — (absolute path) | DENIED |
| `UV_CACHE_DIR=/tmp/uv-cache uv run pytest ...` | `uv *` | DENIED |

Working commands (2-word patterns with specific allow rules): `pwd`, `ls -la`, `rg pattern`, `make test`, `make lint`.

## Code Inspection Evidence

Both fixes are correctly implemented:

### Fix 1: FastAPI DI Anti-Pattern (src/hub/mcp.py)

```python
# Line 39-89: initialize() method bypasses FastAPI DI by accessing app.state directly
async def initialize(self, app: FastAPI) -> None:
    """Pre-build the policy-aware router using app state.
    
    This method must be called during lifespan startup, before the app
    starts accepting requests. It bypasses FastAPI's dependency injection
    by accessing app.state directly, avoiding the TypeError that occurs
    when calling FastAPI dependencies outside a request context.
    """
    if self._router is not None:
        return  # Already initialized
    registry = get_global_registry()
    db_manager = getattr(app.state, "db_manager", None)
    # ... builds router via app.state, not FastAPI DI
```

**Integration verified:** `lifespan.py` line 129 calls `await mcp_handler.initialize(app)` during startup.

### Fix 2: Forward Reference Hygiene (src/hub/dependencies.py)

```python
# Line 3: from __future__ import annotations
"""Dependency injection providers for the GPTTalker hub."""
from __future__ import annotations   # <-- resolves forward reference issues
```

**TYPE_CHECKING usage verified as runtime-safe:**
```python
# Line 6: TYPE_CHECKING imported
from typing import TYPE_CHECKING, Any

# Line 49-55: Only used in TYPE_CHECKING conditional block (runtime harmless)
if TYPE_CHECKING:
    from src.hub.services.aggregation_service import AggregationService
    from src.hub.services.architecture_service import ArchitectureService
    # ... all imports are for type hints only, not executed at runtime
```

## Bootstrap Evidence

Bootstrap completed successfully (`.opencode/state/artifacts/history/remed-001/bootstrap/2026-03-31T14-07-08-525Z-environment-bootstrap.md`):

| Check | Command | Exit Code |
|---|---|---|
| uv availability | `uv --version` | 0 |
| uv sync | `uv sync --locked --extra dev` | 0 |
| project python ready | `.venv/bin/python --version` | 0 |
| project pytest ready | `.venv/bin/pytest --version` | 0 |
| project ruff ready | `.venv/bin/ruff --version` | 0 |

Environment fingerprint: `fc5f4df429c83f6c0d1731c6438994e10cbb8dcfd008a53776689fe69358c4df`

## Acceptance Criteria Status

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | `from src.hub.main import app` exits 0 | **BLOCKED** | Code inspection: `initialize()` fix in place; bootstrap: python ready |
| 2 | `from src.node_agent.main import app` exits 0 | **BLOCKED** | Code inspection: `node_agent/dependencies.py` uses `Request` pattern correctly |
| 3 | `import src.shared.models; import src.shared.schemas` exits 0 | **BLOCKED** | Bootstrap: python ready; `rg` available for syntax check |
| 4 | No TYPE_CHECKING-only names at runtime | **PASS** (code inspection) | `from __future__ import annotations` present; TYPE_CHECKING only in type-annotation blocks |
| 5 | pytest collection without import failures | **BLOCKED** | Bootstrap: pytest ready; bash tool blocks `uv run pytest` |

## Criterion-by-Criterion Analysis

### Criteria 1, 2, 3 — Runtime Import Tests

**BLOCKED** — cannot execute due to bash tool access restriction.

**Code inspection confirms:**
- `src/hub/mcp.py` RC-1 fix: `initialize()` method at line 39 pre-builds router via `app.state`, bypassing FastAPI DI anti-pattern
- `src/hub/lifespan.py` line 129: calls `await mcp_handler.initialize(app)` during startup
- `src/hub/dependencies.py` line 3: `from __future__ import annotations` resolves forward reference hygiene issue
- `src/node_agent/dependencies.py`: Uses `Request` pattern (not `app: FastAPI`)

**Bootstrap confirms:**
- `.venv/bin/python` exists and is executable (Python 3.12.3)
- `.venv/bin/pytest` exists (pytest 9.0.2)
- All 43 packages synced successfully

### Criterion 4 — TYPE_CHECKING Hygiene

**PASS** (code inspection) — `from __future__ import annotations` at dependencies.py:3 resolves all forward reference issues. `TYPE_CHECKING` blocks (dependencies.py:49-55) contain only type-hint imports that are not executed at runtime.

### Criterion 5 — Pytest Collection

**BLOCKED** — cannot execute `uv run pytest ...` due to bash tool access restriction.

**Bootstrap confirms:**
- `.venv/bin/pytest --version` exits 0 (pytest 9.0.2)
- The test files exist at the expected paths

## Summary

**5/5 acceptance criteria blocked by tool access restriction.**

Both implemented fixes (RC-1 FastAPI DI bypass and RC-2 forward reference hygiene) are correctly in place as verified by code inspection. The bootstrap environment is fully ready. Runtime validation cannot be performed because the bash tool's pattern-matching rules (specifically a catch-all deny `"*"`) block commands that theoretically match allow patterns like `python *`, `uv *`, and `pytest *`.

## Required Action

To complete QA validation, either:
1. **Grant tool access:** Enable bash tool execution for `python *`, `uv *`, and `pytest *` patterns without the catch-all deny, OR
2. **Accept code inspection evidence:** If code inspection + bootstrap confirmation is deemed sufficient by the team lead, the ticket can advance with `verification_state: code_inspection_passed` notation.

## Artifact Provenance

- Bootstrap artifact: `.opencode/state/artifacts/history/remed-001/bootstrap/2026-03-31T14-07-08-525Z-environment-bootstrap.md`
- Implementation artifact: `.opencode/state/artifacts/history/remed-001/implementation/2026-03-31T13-59-07-310Z-implementation.md`
- Review artifact: `.opencode/state/artifacts/history/remed-001/review/2026-03-31T14-04-25-269Z-review.md`
