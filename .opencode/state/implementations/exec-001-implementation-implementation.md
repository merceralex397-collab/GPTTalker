# EXEC-001 Implementation: Fix node-agent FastAPI dependency injection import failure

## Summary
Fixed `src/node_agent/dependencies.py` by replacing the invalid `FastAPI` app injection pattern with the proper `Request` pattern that accesses app state via `request.app`.

## Problem
The original code used `app: FastAPI` as a FastAPI dependency injection parameter:
```python
def get_config(app: FastAPI) -> NodeAgentConfig:
    if not hasattr(app.state, "config") or app.state.config is None:
        raise RuntimeError("Node agent config not initialized")
    return app.state.config
```

This causes `FastAPIError: Invalid args for response field!` at import time because FastAPI cannot properly inject the app instance this way.

## Solution
Changed both dependency functions to accept `request: Request` instead of `app: FastAPI`, and access app state via `request.app`:

```python
def get_config(request: Request) -> NodeAgentConfig:
    app = request.app
    if not hasattr(app.state, "config") or app.state.config is None:
        raise RuntimeError("Node agent config not initialized")
    return app.state.config
```

This is the standard FastAPI pattern for accessing app state in dependency functions.

## File Changes

**File: `src/node_agent/dependencies.py`**

```diff
 """Dependency injection providers for the node agent."""
 
-from fastapi import Depends, FastAPI
+from fastapi import Request
 
 from src.node_agent.config import NodeAgentConfig
 from src.node_agent.executor import OperationExecutor
 
 
-def get_config(app: FastAPI) -> NodeAgentConfig:
+def get_config(request: Request) -> NodeAgentConfig:
     """Get node agent configuration from app state.
 
     Args:
-        app: The FastAPI application instance.
+        request: The FastAPI request object.
 
     Returns:
         NodeAgentConfig instance stored in app state.
 
     Raises:
         RuntimeError: If config is not initialized in app state.
     """
+    app = request.app
     if not hasattr(app.state, "config") or app.state.config is None:
         raise RuntimeError("Node agent config not initialized")
     return app.state.config
 
 
-def get_executor(app: FastAPI) -> OperationExecutor:
+def get_executor(request: Request) -> OperationExecutor:
     """Get operation executor from app state.
 
     Args:
-        app: The FastAPI application instance.
+        request: The FastAPI request object.
 
     Returns:
         OperationExecutor instance stored in app state.
 
     Raises:
         RuntimeError: If executor is not initialized in app state.
     """
+    app = request.app
     if not hasattr(app.state, "executor") or app.state.executor is None:
         raise RuntimeError("Operation executor not initialized")
     return app.state.executor
```

## Validation Results

### 1. Node-agent import test
**Command:** `uv run python -c "from src.node_agent.main import app"`
**Result:** PASS (exit 0)
**Output:** No errors

### 2. Pytest collection test
**Command:** `uv run pytest tests/ --collect-only -q --tb=no`
**Result:** PASS
**Output:** 126 tests collected in 1.89s
- `tests/hub/test_contracts.py` - 33 tests
- `tests/hub/test_routing.py` - 14 tests
- `tests/hub/test_security.py` - 23 tests
- `tests/hub/test_transport.py` - 13 tests
- `tests/node_agent/test_executor.py` - 21 tests
- `tests/shared/test_logging.py` - 22 tests

### 3. Ruff lint check
**Command:** `uv run ruff check src/node_agent/dependencies.py`
**Result:** PASS
**Output:** All checks passed!

## Trust and Security Notes
- The fix preserves all original error handling (RuntimeError when config/executor not initialized)
- No changes to path validation logic
- No widening of trust boundaries
- FastAPI's dependency injection system now properly resolves `Request` objects automatically
- The `health.py` and `operations.py` files require no changes as FastAPI auto-resolves `Request` in dependency functions
