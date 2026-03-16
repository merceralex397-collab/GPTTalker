# CORE-001 Implementation Summary: Node Registry and Node Health Model

## Overview
This implementation adds the hub-side node registry schema enhancements, CRUD paths, and health metadata tracking used to manage machines. It builds on the existing infrastructure from SETUP-003 (SQLite persistence) and SETUP-004 (FastAPI hub shell).

## Changes Made

### New Files Created

#### 1. `src/hub/services/node_health.py`
- **NodeHealth** class with explicit health metadata including:
  - `health_status`: Current health status (healthy/unhealthy/offline/unknown)
  - `last_health_check`: Last successful health check time
  - `last_health_attempt`: Last health check attempt time
  - `health_latency_ms`: Response latency in milliseconds
  - `health_error`: Error message if check failed
  - `health_check_count`: Total health checks performed
  - `consecutive_failures`: Number of consecutive failures
  - Computed properties: `is_stale` (5 min threshold), `should_retry` (max 3 failures)

- **NodeHealthService** class with:
  - `check_node_health(node: NodeInfo)`: Performs HTTP health check on a single node
  - `check_all_nodes()`: Checks health of all registered nodes
  - `get_node_health(node_id: str)`: Gets current health metadata for a node
  - Timeout handling (10 seconds default)
  - Proper error handling for timeouts, connection errors, and unexpected errors

#### 2. `src/hub/policy/node_policy.py`
- **NodeAccessResult** dataclass with:
  - `approved`: Boolean indicating if access is approved
  - `node_id`: The node identifier checked
  - `rejection_reason`: Reason for rejection if not approved
  - `health_status`: Current health status if available
  - `warning`: Optional warning message

- **NodePolicy** class implementing fail-closed behavior:
  - `validate_node_access(node_id: str)`: Main entry point for node access control
  - `validate_node_list_access(node_ids: list[str])`: Validates multiple nodes
  - `get_accessible_nodes()`: Gets list of all accessible nodes
  - `check_node_reachable(node_id: str)`: Quick reachability check

- **Decision Matrix**:
  | Node Status | Health Status | Access Result |
  |-------------|---------------|---------------|
  | unknown | - | REJECTED |
  | healthy | healthy | APPROVED |
  | healthy | unhealthy | REJECTED |
  | healthy | unknown | REJECTED |
  | offline | offline | APPROVED (warning) |
  | offline | unhealthy | REJECTED |

#### 3. `src/hub/services/__init__.py`
- Export `NodeHealth` and `NodeHealthService`

#### 4. `src/hub/policy/__init__.py`
- Export `NodePolicy` and `NodeAccessResult`

### Modified Files

#### 1. `src/shared/repositories/nodes.py`
- Added import for `NodeHealthStatus`
- Added health-specific methods:
  - `get_health(node_id: str)`: Get health metadata for a node
  - `update_health(...)`: Update health metadata with all fields
  - `get_with_health(node_id: str)`: Get node with health metadata
  - `list_healthy_nodes()`: List nodes that are healthy or offline

#### 2. `src/shared/schemas.py`
- Added `NodeHealthDetail` response model with comprehensive health metadata

#### 3. `src/hub/dependencies.py`
- Added imports for new classes
- Added DI providers:
  - `get_node_repository()`: Provides NodeRepository
  - `get_node_health_service()`: Provides NodeHealthService
  - `get_node_policy()`: Provides NodePolicy

#### 4. `src/shared/migrations.py`
- Added migration version 2 with health tracking columns:
  - `health_status`
  - `health_latency_ms`
  - `health_error`
  - `health_check_count`
  - `consecutive_failures`
  - `last_health_check`
  - `last_health_attempt`

#### 5. `src/shared/tables.py`
- Updated `SCHEMA_VERSION` from 1 to 2

#### 6. `pyproject.toml`
- Added ignore for B008 (FastAPI Depends in defaults)

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Node registry schema is defined | ✅ | Migration v2 adds health columns to nodes table |
| Health metadata model is explicit | ✅ | NodeHealth class with all fields + computed properties |
| Unknown nodes fail closed | ✅ | NodePolicy.validate_node_access() rejects unknown nodes |

## Technical Details

- **Python 3.11+** with full type hints
- **aiosqlite** for async SQLite operations
- **Pydantic** models for validation
- **Async/await** for all async operations
- **Structured logging** with trace_id support
- **Fail-closed** by default - unknown/unhealthy nodes are rejected

## Integration Points

- Uses existing `DatabaseManager` from SETUP-003
- Uses existing HTTP client from SETUP-004
- Integrates with existing `NodeRepository`
- Health columns added via migration system

## Validation

All modified files pass lint checks:
```bash
ruff check src/hub/services/ src/hub/policy/ src/shared/repositories/nodes.py src/shared/migrations.py src/hub/dependencies.py src/shared/schemas.py
# All checks passed!
```

---

## Post-Review Fix (2026-03-16)

### Issue Fixed: Incorrect Latency Measurement

**Location**: `src/hub/services/node_health.py` lines 150-154

**Problem**: The latency calculation used `timeout.connect_time` which is not a valid httpx attribute after request completion.

**Fix Applied**:
```python
# Before (incorrect):
with self._client.timeout(self.DEFAULT_TIMEOUT) as timeout:
    response = await self._client.get(url)
    latency_ms = int(timeout.connect_time * 1000) if timeout.connect_time else None

# After (correct):
response = await self._client.get(
    url,
    timeout=httpx.Timeout(self.DEFAULT_TIMEOUT),
)
latency_ms = int(response.elapsed.total_seconds() * 1000)
```

**Rationale**:
- `response.elapsed` is the correct httpx attribute for measuring total request latency
- Removed incorrect `with` context manager usage on the timeout
- Now correctly measures end-to-end latency including connection, response, and transfer time

### Additional Notes

- **trace_id propagation**: The logging module (`src/shared/logging.py`) already automatically includes trace_id from context via `get_trace_id()`. No additional changes needed.
- **NodeHealthDetail schema**: The schema in `schemas.py` is preserved for potential future use in detailed health endpoint responses.
