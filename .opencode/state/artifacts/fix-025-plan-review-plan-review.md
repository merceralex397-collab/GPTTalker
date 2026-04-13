# Plan Review — FIX-025

## Decision: APPROVED

---

## Review Summary

The planning artifact for FIX-025 is ** APPROVED **. All findings confirm the root cause, implementation steps, dependencies, and acceptance criteria are correct, complete, and sufficient.

---

## Evidence Checkpoints

### 1. Root Cause — ✅ ACCURATE

**Evidence from `src/hub/mcp.py:90`:**
```python
node_policy = NodePolicy(node_repo, None) if node_repo else None
```
The second argument (`health_service`) is `None`. `NodePolicy.__init__` stores this as `self._health` (line 55 of `node_policy.py`). `validate_node_access()` at line 88 then calls:
```python
health = await self._health.get_node_health(node_id)
```
Since `self._health` is `None`, this raises `AttributeError: 'NoneType' object has no attribute 'get_node_health'` for every node-scoped tool call.

---

### 2. Implementation Steps — ✅ CORRECT AND SUFFICIENT

**Step 1 — Construct `NodeHealthService` with available dependencies:**

The planning artifact's proposed construction:
```python
auth_handler = NodeAuthHandler(config.node_client_api_key) if config else None
node_health_service = NodeHealthService(
    node_repo=node_repo,
    http_client=http_client,
    auth_handler=auth_handler,
) if node_repo and http_client else None
```

**Verified against source:**
- `node_repo` is available at line 82: `node_repo = NodeRepository(db_manager) if db_manager else None`
- `http_client` is available at line 57: `http_client = getattr(app.state, "http_client", None)`
- `config` is available at line 58: `config = getattr(app.state, "config", None)`
- `NodeAuthHandler` is imported at line 68 (inside `initialize()`)
- `NodeHealthService` is imported at line 72 (inside `initialize()`)

**Verified against `NodeHealthService.__init__` signature** (`node_health.py:119-124`):
```python
def __init__(
    self,
    node_repo: NodeRepository,
    http_client: httpx.AsyncClient,
    auth_handler: NodeAuthHandler | None = None,
):
```
Keyword arguments `node_repo`, `http_client`, `auth_handler` match exactly.

**Step 2 — Pass real instance to NodePolicy:**

```python
node_policy = NodePolicy(node_repo, node_health_service) if node_repo else None
```
This is a single-line substitution replacing `None` with the constructed service. Correct.

---

### 3. Blockers and Missing Dependencies — ✅ NONE

- No new imports required — `NodeAuthHandler` and `NodeHealthService` are already imported inside `initialize()`
- No new dependencies introduced
- No architectural decisions required
- No other files need modification
- Pattern is consistent with existing `HubNodeClient` construction at `mcp.py:112-118` which also uses `NodeAuthHandler(config.node_client_api_key)`

---

### 4. Acceptance Criteria — ✅ TESTABLE AND COMPLETE

| # | Criterion | Verification |
|---|---|---|
| 1 | NodeHealthService constructed with `node_repo`, `http_client`, `auth_handler` | Code inspection: Step 1 of fix creates exactly this |
| 2 | NodePolicy receives real NodeHealthService instead of None | Code inspection: Step 2 replaces `None` with `node_health_service` |
| 3 | Node-scoped tools no longer raise `'NoneType' object has no attribute 'get_node_health'` | Root cause eliminated — `_health` is never `None` after fix |
| 4 | Import validation exits 0 | Build verification command in validation plan |
| 5 | `list_nodes` continues to work | Confirmed: `list_nodes_impl` (`discovery.py:50-104`) uses `node_repo` directly, never touches `NodePolicy` |

---

### 5. Regression Risk — ✅ NO RISK TO UNAFFECTED TOOLS

- `list_nodes` handler uses `node_repo.list_all()` and `node_repo.get_health()` directly — no `NodePolicy` involvement
- Fix is isolated to `MCPProtocolHandler.initialize()` which runs at startup only
- No changes to any handler functions
- The `PolicyEngine` condition at lines 97-106 already handles `None` for `node_policy` gracefully (it checks `all(p is not None ...)`), so the `policy_engine` will simply be `None` if `node_health_service` construction is skipped due to guard conditions

---

### 6. Risk Table Review

| Risk | Likelihood | Mitigation | Assessment |
|---|---|---|---|
| `config` is `None` | Low — set earlier in lifespan | Guard with `if config` | ✅ Handled |
| `http_client` is `None` | Low | Guard with `if node_repo and http_client` | ✅ Handled |
| Constructor signature changed | Low | Signature stable since CORE-001; verify import resolves | ✅ Valid concern, low probability |

---

## Conclusion

The plan is **decision-complete** with no blockers, no required revisions, and no test changes. The two-step fix (construct `NodeHealthService` then pass to `NodePolicy`) is the minimal, correct solution. All five acceptance criteria are verifiable via code inspection or the stated validation commands.

**No plan revisions are required.**
