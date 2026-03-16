# QA Verification: CORE-004 - Hub-to-node client, auth, and health polling

## Ticket Information
- **ID**: CORE-004
- **Title**: Hub-to-node client, auth, and health polling
- **Wave**: 1
- **Lane**: node-connectivity
- **Status**: QA

## Acceptance Criteria Verification

### Criterion 1: Hub-to-node auth model is enforced ✓

**Verification Method**: Code inspection of `src/hub/services/auth.py` and `src/hub/services/node_client.py`

**Findings**:
- `NodeAuthHandler.get_headers()` adds `Authorization: Bearer {api_key}` header (auth.py:43)
- `HubNodeClient.request()` always includes auth headers via `self._auth.get_headers()` (node_client.py:65)
- `validate_response()` checks for 401/403 status codes and raises `NodeAuthError` (auth.py:58-72)
- Auth headers are always included - no bypass path exists

**Status**: PASS

---

### Criterion 2: HTTP client timeouts are explicit ✓

**Verification Method**: Code inspection of `src/hub/config.py`, `src/hub/lifespan.py`, and `src/hub/services/node_client.py`

**Findings**:
- Config settings defined with explicit defaults:
  - `node_client_timeout: float = 30.0` (config.py:37-39)
  - `node_client_connect_timeout: float = 5.0` (config.py:40-42)
- HTTP client initialized with timeouts in lifespan (lifespan.py:47-56):
  - `timeout=httpx.Timeout(config.node_client_timeout, connect=config.node_client_connect_timeout)`
- HubNodeClient uses configurable timeouts (node_client.py:28-42)
- Health check uses explicit 10-second timeout (node_client.py:151)

**Status**: PASS

---

### Criterion 3: Health polling integrates with the node registry ✓

**Verification Method**: Code inspection of `src/hub/services/node_health.py` and `src/hub/dependencies.py`

**Findings**:
- `NodeHealthService.__init__` accepts `node_repo: NodeRepository` (node_health.py:121)
- `check_all_nodes()` fetches all nodes from registry: `nodes = await self._repo.list_all()` (node_health.py:253)
- Health updates are persisted back to registry: `await self._repo.update_health(...)` (node_health.py:234-243)
- DI wiring in dependencies.py properly connects:
  - NodeRepository → NodeHealthService (dependencies.py:126-151)
  - Auth handler passed to health service (dependencies.py:146-151)

**Status**: PASS

---

## Code Quality Observations

### Strengths
1. Complete separation of concerns: auth handler, HTTP client, and health service are modular
2. Configurable timeouts at multiple levels (global, per-request)
3. Comprehensive error handling in health checks (timeout, connection error, HTTP errors)
4. Proper DI pattern with runtime validation (checks for initialized state)
5. Structured logging with trace IDs

### Minor Observations
1. No retry logic in HubNodeClient (health service has retry logic internally) - not a blocker
2. Health polling is pull-based (no push from nodes) - design decision, not a blocker

---

## Validation Commands

```bash
# Lint check
ruff check src/hub/services/node_client.py src/hub/services/auth.py src/hub/services/node_health.py src/hub/config.py src/hub/lifespan.py src/hub/dependencies.py

# Import check
python -c "from src.hub.services.node_client import HubNodeClient; from src.hub.services.auth import NodeAuthHandler; from src.hub.services.node_health import NodeHealthService; print('All imports OK')"
```

---

## Summary

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| Hub-to-node auth model enforced | PASS | Bearer token in headers, 401/403 validation |
| HTTP client timeouts explicit | PASS | Config settings, lifespan initialization, per-request timeouts |
| Health polling integrates with node registry | PASS | NodeRepository used for fetch/persist, DI wired correctly |

**Overall QA Status**: PASS

All three acceptance criteria verified via code inspection. The implementation correctly:
1. Enforces Bearer token authentication on all hub-to-node requests
2. Provides explicit, configurable timeouts at multiple levels
3. Integrates health polling with the node registry through the repository pattern

No blockers identified.
