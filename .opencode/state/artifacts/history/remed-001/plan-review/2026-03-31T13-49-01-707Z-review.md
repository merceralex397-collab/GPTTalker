# Plan Review: REMED-001

## Decision: APPROVED WITH ISSUES

## Summary

The plan correctly diagnoses the concrete FastAPI DI anti-pattern in `mcp.py` that would cause runtime crashes and proposes a sound remediation strategy. The Step-3 acceptance verification provides a safety net for any residual import issues. However, the plan has two implementation-level gaps that implementers must resolve: the lifespan router-initialization strategy needs explicit specification, and the `list_tools` route endpoint needs a `Request` parameter update.

---

## Findings

### ✅ RC-1 Diagnosis is Accurate

Code inspection confirms `src/hub/mcp.py:53` calls `await get_policy_engine()` directly without FastAPI's dependency-injection context:

```python
# mcp.py:50-53
from src.hub.dependencies import get_policy_engine
policy_engine = await get_policy_engine()  # ← TypeError at runtime
```

`get_policy_engine()` in `dependencies.py:467` has FastAPI `Depends()` parameters:

```python
async def get_policy_engine(
    node_policy: NodePolicy = Depends(get_node_policy),   # needs DI context
    repo_policy: RepoPolicy = Depends(get_repo_policy),
    ...
) -> PolicyEngine:
```

When called outside FastAPI's DI framework (i.e., directly via `await`), the `Depends()` wrappers do not resolve their dependency chains. Each inner dependency (e.g., `get_node_repository` → `get_db_manager` → `request.app.state.db_manager`) requires a `request: Request` parameter to access `request.app.state`. The direct call would raise `TypeError: missing 'request' argument`.

**Impact confirmed**: Hub starts, routes load, but every MCP tool call via `call_tool → handle_tool_call → _ensure_router()` crashes before reaching any handler. `list_tools` also crashes.

---

### ✅ RC-2 Diagnosis is Correct but Low-Risk

`mcp.py:65` uses `"DatabaseManager | None"` as a string annotation. Python 3.11 does not evaluate string annotations at definition time without `from __future__ import annotations`. The default is `None`, so no runtime evaluation occurs unless the function is called with an explicit non-None value. Pattern is fragile but not blocking. Step 2's cleanup is appropriate.

---

### ⚠️ Gap 1: Lifespan Router Initialization Not Fully Specified

The plan's **preferred approach** (Option A) requires pre-building the `PolicyAwareToolRouter` during lifespan and storing it in `app.state`. However:

- The plan does not specify **how** to construct the router in lifespan, since `get_policy_aware_router(request)` requires a live `request` object with `app.state.db_manager` populated.
- The plan lists `lifespan.py` in "Files to Modify" but does not describe the initialization steps.
- The proposed code sketch in `_ensure_router` tries to fall back to `get_policy_aware_router(request)` when `app.state.policy_engine` is absent, but this fallback has the same DI problem it is trying to solve (calling a DI factory without FastAPI context).

**Recommended resolution** (implementer must decide):
- **Option A1 (cleanest)**: In `lifespan.py`, after `app.state.db_manager` is set, manually construct a `PolicyEngine` and `PolicyAwareToolRouter` using the already-initialized app-state objects, then store the router on `app.state`. `_ensure_router` retrieves from `app.state` without needing a per-request `request` object.
- **Option A2**: Pass `Request` to the `list_tools` FastAPI route so all call paths have request context.

---

### ⚠️ Gap 2: `list_tools` Route Endpoint Lacks `Request` Parameter

The plan correctly identifies that `handle_tool_call` needs a `request` parameter (passed from `call_tool` in `routes.py`, which already has `req: Request`). However:

- `routes.py:48` — `list_tools()` has no `Request` parameter.
- `mcp.py:162` — `list_tools()` calls `_ensure_router()` without a request.
- If `list_tools` is called before any `handle_tool_call` (e.g., at startup or via a health check), the router has not been built yet, and `_ensure_router()` will fail for the same DI reason.

The fix requires modifying `routes.py` to inject `Request` into `list_tools` and forwarding it through `mcp_handler.list_tools(request)`.

---

### ✅ Acceptance Criteria Coverage

| AC | Description | Coverage |
|---|---|---|
| AC-1 | `from src.hub.main import app` exits 0 | Covered by Step 3 |
| AC-2 | `from src.node_agent.main import app` exits 0 | Covered by Step 3 |
| AC-3 | `import src.shared.models; import src.shared.schemas` exits 0 | Covered by Step 3 |
| AC-4 | No TYPE_CHECKING leaks or invalid DI parameter types | Covered by Step 2 + code inspection in Step 3 |
| AC-5 | pytest collection without import failures | Covered by Step 3 |

Step 3's "fix any remaining import issues" table is comprehensive and includes all common failure patterns (missing modules, DI errors, TYPE_CHECKING leaks, circular imports, invalid `Depends[]` syntax).

---

### ✅ uv Constraint Compliance

All validation commands correctly use `UV_CACHE_DIR=/tmp/uv-cache uv run` prefix. The plan explicitly forbids bypassing uv with raw pip or system Python.

---

### ✅ Security Boundaries Preserved

The fix is entirely within the hub's internal DI and router initialization. No trust boundary changes, no new external inputs, no path validation modifications.

---

## Required Revisions

**None required at plan level.** The plan is decision-complete for a skilled implementer. However, implementers must resolve the following before or during implementation:

1. **Clarify lifespan initialization**: Specify exactly how `PolicyAwareToolRouter` is constructed in `lifespan.py` and stored on `app.state`, or adopt Option A2 (passing `Request` to `list_tools`).

2. **Update `list_tools` route signature**: Add `Request` parameter to `routes.py:list_tools` and forward it through `mcp_handler.list_tools(request)` so the router can be built on demand when `list_tools` is the first call.

3. **Clarify the `_ensure_router` fallback**: If the intent is to fall back to `get_policy_aware_router(request)` when `app.state` lacks the pre-built router, this needs a live `request` object — which means both call sites (`handle_tool_call` and `list_tools`) must always provide one.

---

## Validation Gaps

- **Router initialization without a live request**: The pre-build-in-lifespan approach requires constructing the router using app-state objects directly (bypassing the `request`-dependent DI factories), which is not explicitly documented.
- **Edge case: `list_tools` called before any tool call**: Without pre-built router or `Request` in the `list_tools` endpoint, the first `list_tools` call would crash.

These are **implementation-level gaps**, not plan-level blockers. Step 3's acceptance verification will catch any failures and trigger targeted fixes per the plan's Step 4 table.

---

## Blockers

None. Bootstrap is ready, diagnosis is accurate, remediation direction is sound, and the Step-3 verification gate provides a safety net for residual issues.
