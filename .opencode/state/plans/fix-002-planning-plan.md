# Implementation Plan: FIX-002 - Fix Depends[] type subscript error in node agent

## Ticket Summary

Fix the `TypeError` raised when importing `src.node_agent.dependencies` because `ConfigDep = Depends[NodeAgentConfig]` and `ExecutorDep = Depends[OperationExecutor]` use `Depends` as a generic type, which is invalid. `Depends` is a function, not a generic type.

## Issue Analysis

The current code at lines 44-46:
```python
ConfigDep = Depends[NodeAgentConfig]
ExecutorDep = Depends[OperationExecutor]
```

This raises: `TypeError: 'typing._GenericAlias' object is not callable`

`Depends` from FastAPI is a callable function/class that should be called with a dependency function, not subscripted like a generic type.

## Proposed Fix

Remove the invalid type aliases and use proper FastAPI dependency injection patterns:

**Option 1 (recommended):** Remove type aliases and use `Depends(get_config)` directly in route handlers.

**Option 2:** If type aliases are desired, use `Callable`:
```python
from typing import TypeAlias

ConfigDep: TypeAlias = Callable[[], NodeAgentConfig]
ExecutorDep: TypeAlias = Callable[[], OperationExecutor]
```

## Implementation Steps

1. **Read** `src/node_agent/dependencies.py` to understand current usage
2. **Identify** all usages of `ConfigDep` and `ExecutorDep` in route handlers
3. **Fix** the type aliases:
   - Option A: Remove them and update route handlers to use `Depends(get_config)` and `Depends(get_executor)`
   - Option B: Change to `Callable` type aliases
4. **Verify** import works: `python3 -c 'from src.node_agent.dependencies import *'`
5. **Test** route handlers still work correctly with FastAPI DI

## Acceptance Criteria

- [ ] `python3 -c 'from src.node_agent.dependencies import *'` succeeds without TypeError
- [ ] Node agent routes using ExecutorDep/ConfigDep work correctly with FastAPI DI
- [ ] No TypeError at import time

## Risk Assessment

- **Risk level**: Low
- **Impact**: Blocking issue that prevents node agent import
- **Mitigation**: Simple type annotation fix, no behavioral changes

## Dependencies

None - standalone bugfix.
