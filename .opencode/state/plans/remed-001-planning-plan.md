# Plan: REMED-001 — Restore Runtime-Safe Imports

## Ticket
- **ID:** REMED-001
- **Title:** One or more Python packages fail to import — the service cannot start
- **Wave:** 12
- **Lane:** runtime
- **Stage:** planning

---

## Diagnosis Summary

### Source Finding (EXEC001)
Diagnosis pack `diagnosis/20260331-125921` documented three `ModuleNotFoundError` failures at runtime:
- `src.hub`: `ModuleNotFoundError: No module named 'pydantic'`
- `src.node_agent`: `ModuleNotFoundError: No module named 'uvicorn'`
- `src.shared`: `ModuleNotFoundError: No module named 'pydantic'`

### Current Environment State
- **Bootstrap status:** PASS (`.opencode/state/artifacts/history/remed-001/bootstrap/2026-03-31T13-35-57-474Z-environment-bootstrap.md`)
- `uv sync --locked --extra dev` exits 0
- Python, pytest, and ruff all available via `.venv`
- All packages resolved and checked

The diagnosis errors appear to have been stale environment state. However, code inspection reveals **one concrete runtime DI bug** that would prevent the hub from starting, plus potential follow-on issues once runtime import chains are exercised.

---

## Root Cause Analysis

### RC-1: `mcp.py` calls FastAPI dependency factory without DI context (concrete bug)

**File:** `src/hub/mcp.py`, lines 50–53

```python
# Lines 50-53 — WRONG: calling FastAPI dependency directly
from src.hub.dependencies import get_policy_engine

policy_engine = await get_policy_engine()   # ← RuntimeError: get_policy_engine()
                                           #   has FastAPI Depends() params
                                           #   (node_policy, repo_policy, etc.)
                                           #   that are not provided when called directly
```

`get_policy_engine()` in `src/hub/dependencies.py:467` is a FastAPI dependency factory:
```python
async def get_policy_engine(
    node_policy: NodePolicy = Depends(get_node_policy),   # Requires request.app.state
    repo_policy: RepoPolicy = Depends(get_repo_policy),
    write_target_policy: WriteTargetPolicy = Depends(get_write_target_policy),
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),
) -> PolicyEngine:
```

When called directly via `await get_policy_engine()`, FastAPI's `Depends()` injection does not run. Each inner dependency (`get_node_policy`, `get_repo_policy`, etc.) requires a `request: Request` parameter to access `request.app.state`. Calling it directly causes a **runtime TypeError** (missing positional argument `request`).

**Impact:** The hub will start and routes will load, but every MCP tool call via `call_tool` → `handle_tool_call` → `_ensure_router()` will crash before reaching any tool handler.

**Fix required:** Refactor `_ensure_router` to use the already-initialized `PolicyAwareToolRouter` from `get_policy_aware_router` (a properly FastAPI-injected dependency), OR pass the `request` object through so the full DI chain can resolve.

---

### RC-2: `mcp.py` forward reference without `TYPE_CHECKING` guard

**File:** `src/hub/mcp.py`, line 65

```python
db_manager: "DatabaseManager | None" = None,
```

The string forward reference `"DatabaseManager | None"` appears at module level inside a method body (not a TYPE_CHECKING block). In Python 3.11+, `from __future__ import annotations` is NOT active in `mcp.py`, so this string annotation is evaluated at runtime as `eval("DatabaseManager | None")`. `DatabaseManager` is only imported under `if TYPE_CHECKING:` at line 17 — meaning at **runtime this eval would raise `NameError`**.

Note: Since this is a default parameter value (`= None`), Python does NOT evaluate it at function definition time — it evaluates the default at call time. So this particular line would only fail if the function is called with the default, and even then only if the string annotation is somehow forced to evaluate. The risk is low but the pattern is incorrect.

**Fix:** Move `DatabaseManager` to the module-level `TYPE_CHECKING` block (line 16-17) where it is already partially present, or change the annotation to a concrete type.

---

### RC-3: Runtime import chain completeness

The diagnosis pack's original `ModuleNotFoundError` failures indicate the uv environment lacked packages at diagnosis time. The bootstrap now succeeds, but a chain-verification step is required to confirm all import paths that would be exercised at runtime are actually working in the current environment.

The primary import chains to verify:
1. `src.hub.main:app` → lifespan → `tunnel_manager` → `HubConfig`
2. `src.hub.main:app` → routes → `handlers` → `mcp` → `dependencies`
3. `src.node_agent.main:app` → lifespan → `OperationExecutor` → `allowed_paths`
4. `src.shared.models` → pydantic imports

---

## Implementation Steps

### Step 1: Fix `mcp.py` DI anti-pattern (RC-1)

**File:** `src/hub/mcp.py`

The cleanest fix is to inject the router via FastAPI's `Depends()` when `handle_tool_call` is invoked, rather than building the router inline in `_ensure_router`.

**Approach A (preferred):** Use `get_policy_aware_router` from `dependencies.py` via `Depends()`. Since `handle_tool_call` is NOT a FastAPI route handler but an internal method, we need to pass the request through:

```python
# In call_tool (routes.py), pass request to handle_tool_call:
result = await mcp_handler.handle_tool_call(
    request=req,   # ← add request parameter
    tool_name=request.tool_name,
    ...
)

# In mcp.py:
async def handle_tool_call(
    self,
    request: Request,   # ← new required parameter
    tool_name: str,
    ...
):
    ...
    router = await self._ensure_router(request)  # ← pass request
```

And in `_ensure_router(request: Request)`:
```python
async def _ensure_router(self, request: Request) -> PolicyAwareToolRouter:
    if self._router is None:
        registry = get_global_registry()
        # policy_engine needs request-scoped DI — get from app state directly:
        engine: PolicyEngine | None = getattr(request.app.state, 'policy_engine', None)
        if engine is None:
            # Fall back: build via get_policy_aware_router with request
            from src.hub.dependencies import get_policy_aware_router
            engine = await get_policy_aware_router(request)
        self._router = PolicyAwareToolRouter(registry=registry, policy_engine=engine)
    return self._router
```

Or simpler: pre-build the router at startup (in `lifespan`) and store it on `app.state`, then `_ensure_router` just retrieves it. This avoids per-request router reconstruction.

**Verify after fix:**
```
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.mcp import MCPProtocolHandler; print('OK')"
```

---

### Step 2: Fix `mcp.py` forward reference (RC-2)

**File:** `src/hub/mcp.py`

Move `DatabaseManager` to the module-level TYPE_CHECKING block (already partially there):

```python
# Line 16-17 currently:
if TYPE_CHECKING:
    from src.shared.database import DatabaseManager   # ← already correct
```

The annotation at line 65 uses `"DatabaseManager | None"` as a string, which is fine for forward refs — Python 3.11 does not eval string annotations. The real concern is the pattern is fragile. Ensure no runtime evaluation of this string occurs. **No change strictly required** but the pattern should be cleaned up.

---

### Step 3: Run full acceptance verification

Execute all five acceptance criteria commands:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "import src.shared.models; import src.shared.schemas"
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.tools import register_all_tools; print('OK')"
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py tests/node_agent/test_executor.py --collect-only -q
```

For each failure, inspect the traceback to identify:
- Missing module → install via `pyproject.toml` dependency addition
- DI error → fix dependency injection pattern
- TYPE_CHECKING leak → add `TYPE_CHECKING` guard or string annotation
- Circular import → refactor import to function-local scope

---

### Step 4: Fix any remaining import issues

Based on Step 3 results, apply targeted fixes. Common patterns:

| Pattern | Fix |
|---|---|
| `from pydantic import ...` at module level but pydantic not installed | Verify `pydantic` is in `pyproject.toml` dependencies |
| `from module import Class` where Class uses pydantic at runtime | Check `module.__init__` or `module.models` for lazy imports |
| Circular `import` between two modules | Move one import inside the function/method that needs it |
| `Depends[SomeType]` (generic subscript on Depends) | Use `Depends()` with a callable, not a generic type alias |

---

## Validation Plan

1. **AC-1:** `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"` exits 0
2. **AC-2:** `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"` exits 0
3. **AC-3:** `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "import src.shared.models; import src.shared.schemas"` exits 0
4. **AC-4:** All touched runtime annotations and FastAPI dependency functions avoid TYPE_CHECKING-only names and invalid DI parameter types at import time (code inspection of modified files)
5. **AC-5:** `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py tests/node_agent/test_executor.py --collect-only -q` completes without import-time failures

---

## Files to Modify

| File | Change | Reason |
|---|---|---|
| `src/hub/mcp.py` | Refactor `_ensure_router()` to avoid calling `get_policy_engine()` directly; pass `request` through or pre-build router in lifespan | RC-1: FastAPI DI anti-pattern |
| `src/hub/mcp.py` | Clean up `db_manager` forward reference annotation | RC-2: TYPE_CHECKING hygiene |
| `src/hub/lifespan.py` | (If needed) Pre-build `PolicyAwareToolRouter` and store on `app.state` to avoid per-request construction | Simplifies DI chain |

---

## Risks and Assumptions

- **Risk:** The `mcp.py` DI fix may require storing the router or policy engine in `app.state` during startup (lifespan), which is a architectural change. Alternative: pass `request` through the entire call chain.
- **Assumption:** The diagnosis pack's `ModuleNotFoundError` was due to stale environment state, not current code. Acceptance criteria will confirm.
- **Assumption:** No circular imports exist in the current import graph. The full import chain verification in Step 3 will confirm or deny this.
- **Constraint:** Must use `UV_CACHE_DIR=/tmp/uv-cache uv run` for all validation commands. Must not bypass uv with raw pip or system python.

---

## Blockers

None identified at planning stage. Step 3 (acceptance verification) may reveal additional import issues that constitute new blockers.
