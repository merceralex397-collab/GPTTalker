# CORE-004 Implementation Summary

## Overview

Implemented the hub-to-node client infrastructure for communicating with node agents over Tailscale. This includes authentication handling, HTTP client with configurable timeouts, and integration with the node health polling service.

## Files Created

### 1. `src/hub/services/auth.py`
- **`NodeAuthHandler`**: Authentication handler for hub-to-node requests
  - Manages API key-based Bearer token authentication
  - `get_headers()`: Returns auth headers with version and optional Bearer token
  - `validate_response()`: Validates HTTP 401/403 responses for auth failures
  - `NodeAuthError`: Custom exception for auth failures

### 2. `src/hub/services/node_client.py`
- **`HubNodeClient`**: HTTP client for hub-to-node communication
  - Wraps httpx.AsyncClient with auth and timeout handling
  - `request()`: Generic authenticated request method with timeout support
  - `get()` / `post()`: Convenience methods for HTTP GET/POST
  - `health_check()`: Perform health check on a node
  - `read_file()`: Read file from node
  - `write_file()`: Write file to node
  - `search()`: Search within node's repos

## Files Modified

### 1. `src/hub/config.py`
Added new node client configuration fields:
- `node_client_timeout`: Default request timeout (30s)
- `node_client_connect_timeout`: Connect timeout (5s)
- `node_client_pool_max_connections`: Max connections per pool (10)
- `node_client_pool_max_keepalive`: Max keepalive connections (20)
- `node_client_api_key`: Optional API key for node auth

### 2. `src/hub/lifespan.py`
- Added `httpx.AsyncClient` initialization with proper timeout and connection pool limits
- Stores client in `app.state.http_client` for dependency injection
- Properly closes client on shutdown

### 3. `src/hub/dependencies.py`
Added new dependency providers:
- `get_node_auth_handler()`: Returns NodeAuthHandler with config API key
- `get_node_client()`: Returns HubNodeClient instance with HTTP client and auth handler

### 4. `src/hub/services/node_health.py`
- Updated `NodeHealthService` to accept optional `auth_handler` parameter
- Health check requests now include auth headers when handler is provided

## Acceptance Criteria Verification

1. **Hub-to-node auth model is enforced**: ✅
   - NodeAuthHandler manages API key authentication
   - Bearer token included in all requests when API key is configured
   - Response validation checks for 401/403 status codes

2. **HTTP client timeouts are explicit**: ✅
   - All timeouts configurable via HubConfig
   - Default timeout: 30s, Connect timeout: 5s
   - Per-request timeout override available

3. **Health polling integrates with the node registry**: ✅
   - NodeHealthService updated to use auth headers
   - Uses existing NodeRepository for health data persistence
   - Dependency injection provides proper client and auth handler

## Integration Points

| Component | Integration |
|-----------|------------|
| `lifespan.py` | Initializes httpx.AsyncClient with config |
| `dependencies.py` | Provides HubNodeClient and NodeAuthHandler |
| `node_health.py` | Uses auth handler for health checks |
| `config.py` | Provides all timeout and auth configuration |

## Validation

- ✅ All files pass `ruff check`
- ✅ Type hints complete
- ✅ Docstrings present
- ✅ Proper async/await patterns used
- ✅ Fail-closed behavior maintained

## Notes

- The node client assumes nodes are reachable via hostname over Tailscale
- Auth headers are optional - nodes will accept unauthenticated requests if no API key configured
- Connection pooling defaults support a reasonable number of nodes
- The implementation follows the existing patterns in the codebase for config, logging, and DI

---

## Code Review Fixes Applied

### Medium Severity: Config Attribute Mismatch (FIXED)
- **Location**: `src/hub/lifespan.py` line 65
- **Issue**: Referenced `config.database_path` which doesn't exist
- **Fix**: Changed to `config.database_url`

### Low Severity: JSON Parsing Error Handling (FIXED)
- **Location**: `src/hub/services/node_client.py` - `health_check()` method
- **Issue**: Missing error handling for JSON parsing failures
- **Fix**: Added try/except block around `response.json()` with proper logging and error response

### Low Severity: Deprecated datetime.utcnow() (FIXED)
- **Location**: `src/hub/services/node_health.py`
- **Issue**: Deprecated `datetime.utcnow()` usage
- **Fix**: Replaced with `datetime.now(timezone.utc)` in 3 locations:
  - Line 73: `is_stale` property calculation
  - Line 149: `check_node_health()` - last health attempt timestamp
  - Line 175: `check_node_health()` - last successful check timestamp
