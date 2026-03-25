# Plan: EXEC-001 — Fix node-agent FastAPI dependency injection import failure

## Problem Statement

`src/node_agent/dependencies.py` defines two dependency-injection providers:

```python
def get_config(app: FastAPI) -> NodeAgentConfig:
    ...

def get_executor(app: FastAPI) -> OperationExecutor:
    ...
```

Both declare `app: FastAPI` as a direct parameter of a `Depends()` callable. FastAPI's dependency-injection system does not accept a bare `FastAPI` instance as a resolvable dependency — it raises `fastapi.exceptions.FastAPIError: Invalid args for response field!` at import/startup. This breaks `from src.node_agent.main import app` and blocks pytest collection at `tests/node_agent/test_executor.py`.

## Root Cause

FastAPI's `Depends()` resolves dependencies from the request context or from other declared dependency providers. A raw `FastAPI` app instance is not a valid resolvable dependency type — the framework cannot inject it automatically. The correct pattern is to receive `request: Request` from FastAPI's context and access `request.app` to reach the application state.

## Files Affected

| File | Change |
|---|---|
| `src/node_agent/dependencies.py` | Replace `app: FastAPI` with `request: Request` in both `get_config` and `get_executor`; update body to use `request.app.state` |
| `src/node_agent/routes/health.py` | No structural change — the route handler already declares `request: Request`; FastAPI passes it to the dependency automatically |
| `src/node_agent/routes/operations.py` | No structural change — FastAPI auto-resolves `Request` in dependency functions |

## Trust Boundary

The `_validate_path` method in `src/node_agent/executor.py` (lines 30–68) enforces:
- Rejection of absolute paths
- Rejection of `..` path traversal
- Boundary checking against `allowed_paths`

This method is **unchanged**. The DI fix only corrects how `config` and `executor` are retrieved from app state — it does not alter the executor's path validation logic or allowed-path scope.

## Implementation Steps

### Step 1 — Fix `src/node_agent/dependencies.py`

Replace the entire file content (40 lines) with the following:

```python
"""Dependency injection providers for the node agent."""

from fastapi import Depends, Request

from src.node_agent.config import NodeAgentConfig
from src.node_agent.executor import OperationExecutor


def get_config(request: Request) -> NodeAgentConfig:
    """Get node agent configuration from app state.

    Args:
        request: The current FastAPI request object, used to access app state.

    Returns:
        NodeAgentConfig instance stored in app state.

    Raises:
        RuntimeError: If config is not initialized in app state.
    """
    app = request.app
    if not hasattr(app.state, "config") or app.state.config is None:
        raise RuntimeError("Node agent config not initialized")
    return app.state.config


def get_executor(request: Request) -> OperationExecutor:
    """Get operation executor from app state.

    Args:
        request: The current FastAPI request object, used to access app state.

    Returns:
        OperationExecutor instance stored in app state.

    Raises:
        RuntimeError: If executor is not initialized in app state.
    """
    app = request.app
    if not hasattr(app.state, "executor") or app.state.executor is None:
        raise RuntimeError("Operation executor not initialized")
    return app.state.executor
```

**Changes:**
- `from fastapi import Depends, FastAPI` → `from fastapi import Depends, Request`
- `def get_config(app: FastAPI)` → `def get_config(request: Request)`; body uses `request.app.state.config`
- `def get_executor(app: FastAPI)` → `def get_executor(request: Request)`; body uses `request.app.state.executor`

### Step 2 — Verify `src/node_agent/routes/health.py`

The route handler at line 33–38 already declares `request: Request` and `response: Response` as parameters and uses `Depends(get_config)` / `Depends(get_executor)`. No changes are required — FastAPI will automatically provide the `Request` object to the dependency function when it is declared as a parameter.

### Step 3 — Verify `src/node_agent/routes/operations.py`

All five route handlers (`list_dir`, `read_file`, `search`, `git_status`, `write_file`) already declare `executor: OperationExecutor = Depends(get_executor)`. FastAPI auto-resolves `Request` when it appears as a parameter in a dependency callable. No changes are required.

### Step 4 — Validate the fix

Run the following commands and confirm exit code 0:

```bash
# Import must succeed without FastAPIError
.venv/bin/python -c "from src.node_agent.main import app"

# Collection must not abort on node-agent import wiring
.venv/bin/pytest tests/ --collect-only -q --tb=no
```

## Acceptance Criteria Coverage

| Criterion | How Addressed |
|---|---|
| Replace `app: FastAPI` with FastAPI-safe `Request`-based pattern | `get_config(request: Request)` and `get_executor(request: Request)` use `request.app.state` — the correct FastAPI DI pattern |
| `.venv/bin/python -c "from src.node_agent.main import app"` exits 0 | FastAPI no longer receives an unresolvable `FastAPI` type as a `Depends()` parameter |
| No trust-boundary or path-validation changes | `_validate_path` in `executor.py` is untouched |
| pytest collection no longer fails on node-agent import | Import succeeds, so pytest can collect `tests/node_agent/test_executor.py` |

## Validation Plan

1. Apply the file edit to `dependencies.py`
2. Run `python -c "from src.node_agent.main import app"` — must exit 0
3. Run `pytest tests/ --collect-only -q --tb=no` — must exit 0 with no collection errors
4. Run `ruff check src/node_agent/dependencies.py` — must pass with no errors

## Risks and Assumptions

- **Assumption**: FastAPI's dependency injection automatically resolves `Request` when declared as a parameter in a dependency function (a well-established FastAPI pattern). This is confirmed by the existing `health.py` route that already works with `request: Request` in the handler.
- **Risk**: None identified. The fix is a direct, minimal substitution of one parameter type and the access pattern.
- **Side effect**: None. Both `app.state.config` and `app.state.executor` are set by `lifespan.py` before any request is handled, so the `request.app.state` access returns the same objects as before.
