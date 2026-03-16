# CORE-004 Implementation Plan: Hub-to-node client, auth, and health polling

## 1. Scope

This ticket implements the hub-side HTTP client infrastructure for communicating with node agents over Tailscale. It includes authentication, timeout policies, health polling integration, and connection management.

**Acceptance Criteria:**
1. Hub-to-node auth model is enforced
2. HTTP client timeouts are explicit
3. Health polling integrates with the node registry

## 2. Files or Systems Affected

### New Files to Create
- `src/hub/services/node_client.py` — Hub-to-node HTTP client with auth support
- `src/hub/services/auth.py` — Authentication handler for hub-to-node communication

### Files to Modify
- `src/hub/lifespan.py` — Initialize and manage HTTP client lifecycle
- `src/hub/dependencies.py` — Add node client dependency provider
- `src/hub/config.py` — Add node client configuration (timeouts, pool settings)
- `src/hub/services/node_health.py` — Integrate with new node client

### External Dependencies
- `httpx` — Already in dependencies (async HTTP client)

## 3. Implementation Steps

### Step 1: Add Node Client Configuration (HubConfig)

Extend `src/hub/config.py` with new configuration fields:

```python
# Node client settings
node_client_timeout: int = Field(30, ge=1, description="Default node request timeout")
node_client_connect_timeout: float = Field(5.0, ge=0.1, description="Node connect timeout")
node_client_pool_max_connections: int = Field(10, ge=1, description="Max connections per node")
node_client_pool_MAX_KEEPALIVE: int = Field(20, ge=1, description="Max keepalive connections")
node_client_api_key: str | None = Field(None, description="API key for node authentication")
```

### Step 2: Create Authentication Handler

Create `src/hub/services/auth.py`:

```python
class NodeAuthHandler:
    """Handles authentication for hub-to-node requests."""
    
    def __init__(self, api_key: str | None):
        self._api_key = api_key
    
    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for node requests."""
        headers = {"X-GPTTalker-Version": "1.0.0"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers
    
    def validate_response(self, response: httpx.Response) -> None:
        """Validate response authentication."""
        if response.status_code == 401:
            raise NodeAuthError("Node authentication failed")
        if response.status_code == 403:
            raise NodeAuthError("Node authorization failed")
```

### Step 3: Create Hub-to-Node Client

Create `src/hub/services/node_client.py`:

```python
class HubNodeClient:
    """HTTP client for hub-to-node communication over Tailscale."""
    
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        auth_handler: NodeAuthHandler,
        default_timeout: float = 30.0,
        connect_timeout: float = 5.0,
    ):
        self._client = http_client
        self._auth = auth_handler
        self._default_timeout = default_timeout
        self._connect_timeout = connect_timeout
    
    async def request(
        self,
        node: NodeInfo,
        method: str,
        path: str,
        timeout: float | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make authenticated request to node."""
        url = f"http://{node.hostname}{path}"
        headers = self._auth.get_headers()
        headers.update(kwargs.pop("headers", {}))
        
        response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            timeout=timeout or self._default_timeout,
            **kwargs,
        )
        return response
    
    async def get(self, node: NodeInfo, path: str, **kwargs) -> httpx.Response:
        """GET request to node."""
        return await self.request(node, "GET", path, **kwargs)
    
    async def post(self, node: NodeInfo, path: str, **kwargs) -> httpx.Response:
        """POST request to node."""
        return await self.request(node, "POST", path, **kwargs)
    
    async def health_check(self, node: NodeInfo) -> NodeHealthResponse:
        """Perform health check on node."""
        response = await self.get(node, "/health", timeout=10.0)
        # Parse response...
```

### Step 4: Update Hub Lifespan

Modify `src/hub/lifespan.py` to initialize the HTTP client:

```python
# Add to startup:
app.state.http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(config.node_client_timeout, connect=config.node_client_connect_timeout),
    limits=httpx.Limits(
        max_connections=config.node_client_pool_max_connections,
        max_keepalive_connections=config.node_client_pool_MAX_KEEPALIVE,
    ),
)

# Add to shutdown:
if app.state.http_client is not None:
    await app.state.http_client.aclose()
```

### Step 5: Update Dependencies

Modify `src/hub/dependencies.py` to add providers:

```python
async def get_node_client(
    request: Request,
    node_repo: NodeRepository = Depends(get_node_repository),
) -> HubNodeClient:
    http_client: httpx.AsyncClient = request.app.state.http_client
    config: HubConfig = request.app.state.config
    
    auth_handler = NodeAuthHandler(config.node_client_api_key)
    return HubNodeClient(
        http_client=http_client,
        auth_handler=auth_handler,
        default_timeout=config.node_client_timeout,
        connect_timeout=config.node_client_connect_timeout,
    )
```

### Step 6: Enhance NodeHealthService

Modify `src/hub/services/node_health.py` to use the new client:

```python
class NodeHealthService:
    def __init__(
        self,
        node_repo: NodeRepository,
        http_client: httpx.AsyncClient | HubNodeClient,
        auth_handler: NodeAuthHandler | None = None,
    ):
        # Update to use auth headers when calling nodes
```

## 4. Validation Plan

1. **Static Analysis**: Run `ruff check src/hub/services/` to verify code quality
2. **Import Test**: Verify all new modules can be imported without errors
3. **Config Validation**: Ensure HubConfig validates new fields correctly
4. **Unit Tests**: Create tests for:
   - `NodeAuthHandler.get_headers()` — validates header generation
   - `HubNodeClient.request()` — validates request construction
   - `HubNodeClient.health_check()` — validates health response parsing
5. **Integration Test**: Verify health check flow works with mock node

## 5. Risks and Assumptions

### Risks
- **Tailscale DNS**: Assumes nodes are reachable via hostname over Tailscale
- **Auth Propagation**: Auth headers must be validated by node agents (future ticket)
- **Connection Pool**: May need tuning based on node count

### Assumptions
- Node agents run on Linux with HTTP endpoints
- Tailscale provides reliable internal networking
- API key auth is sufficient for initial deployment

## 6. Blockers or Required User Decisions

None — all blocking decisions are resolved:
- Auth model: API key (Bearer token) — follows existing `api_key` field in NodeAgentConfig
- Transport: HTTP over Tailscale — follows canonical brief
- Timeouts: Configurable with sensible defaults — follows existing pattern

## 7. Integration Points

| From | To | Description |
|------|-----|-------------|
| `src/hub/lifespan.py` | `src/hub/services/node_client.py` | Initializes HTTP client |
| `src/hub/dependencies.py` | `src/hub/services/node_client.py` | DI provider |
| `src/hub/services/node_health.py` | `src/hub/services/node_client.py` | Uses for health checks |
| `src/hub/config.py` | All | Provides configuration |
