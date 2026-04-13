# Planning Artifact — FIX-025

## Ticket
- **ID**: FIX-025
- **Title**: Fix NodePolicy None health service wiring in MCP initialize
- **Wave**: 22
- **Lane**: bugfix
- **Finding source**: FIX-024 (post-completion issue)
- **Source mode**: post_completion_issue

---

## 1. Scope

### Files or Systems Affected
- `src/hub/mcp.py` — single file, lines ~89–93

### Systems Impacted
- Hub MCP tool routing — node-scoped tools (list_repos, inspect_repo_tree, read_repo_file, search_repo, git_status) will no longer crash with `AttributeError: 'NoneType' object has no attribute 'get_node_health'`

---

## 2. Root Cause

In `src/hub/mcp.py`, `MCPProtocolHandler.initialize()` at line 90 builds:

```python
node_policy = NodePolicy(node_repo, None) if node_repo else None
```

The second argument (`health_service`) is passed as `None`, but `NodePolicy.validate_node_access()` at line 88 calls:

```python
health = await self._health.get_node_health(node_id)
```

Since `_health` is `None`, every call to a node-scoped tool raises:
`AttributeError: 'NoneType' object has no attribute 'get_node_health'`.

`NodeHealthService` is never constructed in `initialize()`. All required dependencies are already in scope:
- `node_repo: NodeRepository` — already available
- `http_client: httpx.AsyncClient` — already available via `app.state.http_client`
- `auth_handler: NodeAuthHandler | None` — buildable from `config.node_client_api_key`

---

## 3. Implementation Steps

### Step 1 — Construct `NodeHealthService` before `NodePolicy` building

In `src/hub/mcp.py`, before the existing `node_policy = NodePolicy(node_repo, None)` line (line 90), insert:

```python
auth_handler = NodeAuthHandler(config.node_client_api_key) if config else None
node_health_service = NodeHealthService(
    node_repo=node_repo,
    http_client=http_client,
    auth_handler=auth_handler,
) if node_repo and http_client else None
```

### Step 2 — Pass the real health service to `NodePolicy`

Change line 90 from:

```python
node_policy = NodePolicy(node_repo, None) if node_repo else None
```

to:

```python
node_policy = NodePolicy(node_repo, node_health_service) if node_repo else None
```

### Constraints
- No new imports required — `NodeHealthService` and `NodeAuthHandler` are already imported in the file
- No other files need modification
- No new dependencies
- No test changes required

---

## 4. Validation Plan

### Build Verification
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.mcp import MCPProtocolHandler; from src.hub.lifespan import lifespan; print("OK")'
```
Expected: exits 0, prints `OK`

### Smoke Test
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short
```
Expected: all tests pass (no regressions)

### Runtime Validation (if environment permits)
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c "
from src.hub.mcp import MCPProtocolHandler
from src.hub.lifespan import lifespan
from src.hub.dependencies import get_mcp_handler
from src.shared.models import NodeRepository
print('NodeHealthService wiring: OK')
"
```

---

## 5. Risks and Assumptions

### Assumptions
- `NodeHealthService` constructor signature accepts `node_repo`, `http_client`, and `auth_handler` as keyword arguments
- `config.node_client_api_key` is accessible on the `config` object in scope at line 90
- `app.state.http_client` is always an `httpx.AsyncClient` instance (not None) when `http_client` is in scope

### Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| `config` is `None` at that point in initialization | Low — config is set earlier in lifespan | `auth_handler = NodeAuthHandler(config.node_client_api_key) if config else None` handles the null case |
| `http_client` is `None` when `node_repo` is not None | Low | Guard `node_health_service` construction with `if node_repo and http_client` |
| `NodeHealthService` constructor signature changed | Low | Constructor signature is stable from CORE-001; verify import resolves |

### Blockers or Required User Decisions
None — all dependencies are already in scope, no architectural choices required.

---

## 6. Acceptance Criteria Checklist

| # | Criterion | Status |
|---|---|---|
| 1 | NodeHealthService is constructed with `node_repo`, `http_client`, and `auth_handler` in `initialize()` | ✅ planned |
| 2 | NodePolicy receives the real NodeHealthService instance instead of None | ✅ planned |
| 3 | Node-scoped tools no longer fail with `'NoneType' object has no attribute 'get_node_health'` | ✅ fixed by construction |
| 4 | `UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.mcp import MCPProtocolHandler; from src.hub.lifespan import lifespan; print("OK")'` exits 0 | ✅ validation command |
| 5 | list_nodes continues to work correctly (does not use NodePolicy directly) | ✅ unchanged code path |
