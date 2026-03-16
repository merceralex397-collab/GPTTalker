# CORE-001 Implementation Plan: Node Registry and Node Health Model

## 1. Scope

Implement the hub-side node registry schema enhancements, CRUD path, and health metadata tracking used to manage machines. The plan builds on the existing node infrastructure from SETUP-003 (SQLite persistence) and SETUP-004 (FastAPI hub shell).

## 2. Files or Systems Affected

### Existing Files to Modify

| File | Purpose | Changes |
|------|---------|---------|
| `src/shared/models.py` | Node domain models | Add `NodeHealth` model for explicit health metadata |
| `src/shared/repositories/nodes.py` | Node CRUD repository | Add health-specific query methods |
| `src/shared/schemas.py` | API schemas | Add `NodeHealthDetail` response model |
| `src/hub/dependencies.py` | DI providers | Add node repository and health service providers |

### New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/services/node_health.py` | Health polling service with TTL-based status computation |
| `src/hub/policy/node_policy.py` | Fail-closed policy engine for node validation |
| `tests/unit/hub/test_node_health.py` | Unit tests for health service |
| `tests/unit/hub/test_node_policy.py` | Unit tests for fail-closed behavior |

## 3. Schema Design

### Node Registry Table (Existing)

The nodes table already exists from SETUP-003:

```sql
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hostname TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unknown',
    last_seen TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);
```

### New: Health Metadata Extension

Add explicit health tracking columns via migration (version 2):

```sql
ALTER TABLE nodes ADD COLUMN health_status TEXT DEFAULT 'unknown';
ALTER TABLE nodes ADD COLUMN health_latency_ms INTEGER;
ALTER TABLE nodes ADD COLUMN health_error TEXT;
ALTER TABLE nodes ADD COLUMN health_check_count INTEGER DEFAULT 0;
ALTER TABLE nodes ADD COLUMN consecutive_failures INTEGER DEFAULT 0;
```

### NodeHealth Model (New)

```python
class NodeHealth(BaseModel):
    """Explicit health metadata for a node."""
    
    node_id: str = Field(..., description="Node identifier")
    health_status: NodeHealthStatus = Field(NodeHealthStatus.UNKNOWN, description="Computed health status")
    last_health_check: datetime | None = Field(None, description="Last successful health check time")
    last_health_attempt: datetime | None = Field(None, description="Last health check attempt")
    health_latency_ms: int | None = Field(None, description="Last health check latency")
    health_error: str | None = Field(None, description="Last health check error")
    health_check_count: int = Field(0, description="Total health checks performed")
    consecutive_failures: int = Field(0, description="Consecutive health check failures")
    
    # Computed properties
    is_stale: bool = Field(False, description="Whether node has not been seen recently")
    should_retry: bool = Field(True, description="Whether health check should be retried")
```

### NodeHealthStatus Enum (Existing)

Already exists in `schemas.py`:

```python
class NodeHealthStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"
```

## 4. Implementation Steps

### Step 1: Add Health Models

**File: `src/shared/models.py`**

Add `NodeHealth` model with computed properties for staleness and retry logic:

```python
class NodeHealth(BaseModel):
    """Explicit health metadata for a node."""
    node_id: str
    health_status: NodeHealthStatus = NodeHealthStatus.UNKNOWN
    last_health_check: datetime | None = None
    last_health_attempt: datetime | None = None
    health_latency_ms: int | None = None
    health_error: str | None = None
    health_check_count: int = 0
    consecutive_failures: int = 0
    
    @computed_field
    @property
    def is_stale(self) -> bool:
        """Node is stale if not seen in 5 minutes."""
        if not self.last_health_check:
            return True
        return (datetime.utcnow() - self.last_health_check).seconds > 300
    
    @computed_field
    @property
    def should_retry(self) -> bool:
        """Node should be retried if under failure limit."""
        return self.consecutive_failures < 3
```

### Step 2: Create Health Polling Service

**File: `src/hub/services/node_health.py`**

Create service that:
- Polls node health via HTTP GET to `/health` endpoint
- Computes health status based on latency, errors, and TTL
- Updates node record with health metadata
- Uses exponential backoff for failed checks

```python
class NodeHealthService:
    """Service for polling and tracking node health."""
    
    HEALTH_ENDPOINT = "/health"
    DEFAULT_TIMEOUT = 10  # seconds
    MAX_CONSECUTIVE_FAILURES = 3
    STALE_THRESHOLD_SECONDS = 300  # 5 minutes
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        node_repo: NodeRepository,
        http_client: httpx.AsyncClient,
    ):
        self._db = db_manager
        self._repo = node_repo
        self._client = http_client
    
    async def check_node_health(self, node: NodeInfo) -> NodeHealth:
        """Perform health check on a single node."""
        # Implementation details...
    
    async def check_all_nodes(self) -> list[NodeHealth]:
        """Check health of all registered nodes."""
        # Implementation details...
    
    def _compute_health_status(
        self,
        latency_ms: int | None,
        error: str | None,
        last_check: datetime | None,
    ) -> NodeHealthStatus:
        """Compute health status based on response metrics."""
        # Implementation details...
```

### Step 3: Create Fail-Closed Node Policy

**File: `src/hub/policy/node_policy.py`

Create policy engine that enforces fail-closed behavior:

```python
class NodePolicy:
    """Policy engine for node access control - fail closed by default."""
    
    def __init__(self, node_repo: NodeRepository, health_service: NodeHealthService):
        self._repo = node_repo
        self._health = health_service
    
    async def validate_node_access(self, node_id: str) -> NodeAccessResult:
        """Validate access to a node.
        
        Returns:
            NodeAccessResult with approved=True if node is valid and healthy.
            Returns approved=False with rejection_reason if node is unknown or unhealthy.
        """
        # 1. Check if node exists in registry
        node = await self._repo.get(node_id)
        if not node:
            return NodeAccessResult(
                approved=False,
                node_id=node_id,
                rejection_reason="unknown_node",
            )
        
        # 2. Check if node is healthy
        health = await self._health.get_node_health(node_id)
        if health and health.health_status == NodeHealthStatus.UNHEALTHY:
            return NodeAccessResult(
                approved=False,
                node_id=node_id,
                rejection_reason="node_unhealthy",
                health_status=health.health_status,
            )
        
        return NodeAccessResult(approved=True, node_id=node_id)
    
    async def validate_node_list_access(self) -> list[str]:
        """Get list of node IDs that the caller can access.
        
        Returns only nodes that are registered and not explicitly blocked.
        """
        # Implementation...
```

### Step 4: Update Node Repository with Health Methods

**File: `src/shared/repositories/nodes.py`**

Add health-specific methods:

```python
class NodeRepository:
    # ... existing methods ...
    
    async def get_with_health(self, node_id: str) -> tuple[NodeInfo, NodeHealth] | None:
        """Get node with current health metadata."""
        # Implementation...
    
    async def update_health(
        self,
        node_id: str,
        status: NodeHealthStatus,
        latency_ms: int | None = None,
        error: str | None = None,
    ) -> bool:
        """Update health metadata for a node."""
        # Implementation...
    
    async def list_healthy_nodes(self) -> list[NodeInfo]:
        """List nodes that are currently healthy."""
        # Implementation...
```

### Step 5: Add Dependency Injection Providers

**File: `src/hub/dependencies.py`**

Add providers for the new services:

```python
async def get_node_repository(request: Request) -> NodeRepository:
    """Get node repository from app state."""
    db_manager = request.app.state.db_manager
    return NodeRepository(db_manager)


async def get_node_health_service(
    request: Request,
    node_repo: NodeRepository = Depends(get_node_repository),
) -> NodeHealthService:
    """Get node health service from app state or create new instance."""
    # Get or create HTTP client from app state
    http_client = request.app.state.http_client
    return NodeHealthService(
        db_manager=request.app.state.db_manager,
        node_repo=node_repo,
        http_client=http_client,
    )


async def get_node_policy(
    node_repo: NodeRepository = Depends(get_node_repository),
    health_service: NodeHealthService = Depends(get_node_health_service),
) -> NodePolicy:
    """Get node policy engine."""
    return NodePolicy(node_repo, health_service)
```

### Step 6: Create Database Migration

**File: `src/shared/migrations.py`**

Add migration for health columns:

```python
MIGRATIONS: dict[int, list[str]] = {
    1: [...],  # Existing
    2: [
        "ALTER TABLE nodes ADD COLUMN health_status TEXT DEFAULT 'unknown';",
        "ALTER TABLE nodes ADD COLUMN health_latency_ms INTEGER;",
        "ALTER TABLE nodes ADD COLUMN health_error TEXT;",
        "ALTER TABLE nodes ADD COLUMN health_check_count INTEGER DEFAULT 0;",
        "ALTER TABLE nodes ADD COLUMN consecutive_failures INTEGER DEFAULT 0;",
    ],
}
```

Update `SCHEMA_VERSION = 2`.

## 5. Integration Points

### With SETUP-003 (SQLite Persistence)
- Node repository already exists and will be extended
- Migration system already in place

### With SETUP-004 (FastAPI Hub Shell)
- Health service uses httpx for HTTP calls to nodes
- Dependency injection pattern already established

### With CORE-004 (Hub-to-Node Connectivity)
- Health service will use the same HTTP client pattern
- Will integrate with node connection pooling

### With CORE-005 (Policy Engine)
- Node policy will be a specialized policy for node access
- CORE-005 will integrate this into the general policy system

## 6. Fail-Closed Behavior Implementation

The fail-closed behavior is implemented in `NodePolicy.validate_node_access()`:

1. **Unknown nodes rejected**: If node_id is not in registry, return immediately with `approved=False`
2. **Unhealthy nodes rejected**: If health status is UNHEALTHY, return with `approved=False`
3. **Offline nodes allowed with warning**: OFFLINE nodes are allowed but logged
4. **Unknown health defaults to blocked**: If health is UNKNOWN, treat as potentially unhealthy

```python
# Decision matrix
| Node Status | Health Status | Access Result |
|-------------|---------------|---------------|
| unknown     | -             | REJECTED      |
| healthy     | healthy       | APPROVED      |
| healthy     | unhealthy     | REJECTED      |
| healthy     | unknown       | REJECTED      |
| offline     | offline       | APPROVED (warning) |
| offline     | unhealthy     | REJECTED      |
```

## 7. Test Considerations

### Unit Tests

1. **test_node_health_computation**: Verify status computation from latency/error
2. **test_stale_detection**: Verify is_stale property
3. **test_fail_closed_unknown_node**: Verify unknown nodes are rejected
4. **test_fail_closed_unhealthy_node**: Verify unhealthy nodes are rejected
5. **test_health_update_persists**: Verify health metadata is stored

### Integration Tests

1. **test_health_polling_cycle**: Full health check cycle
2. **test_policy_enforcement**: Policy blocks access to invalid nodes

### Test Fixtures

Add to `tests/conftest.py`:
- `mock_node_health_service`: Mock health service
- `mock_node_policy`: Mock policy with known outcomes

## 8. Validation Plan

### Acceptance Criteria Verification

| Criterion | Verification Method |
|-----------|---------------------|
| Node registry schema is defined | Schema migration runs, table exists with health columns |
| Health metadata model is explicit | NodeHealth model exists with all fields |
| Unknown nodes fail closed | Unit test verifies rejection |

### Validation Commands

```bash
# Run unit tests
pytest tests/unit/hub/test_node_health.py tests/unit/hub/test_node_policy.py -v

# Run lint
ruff check src/hub/services/ src/hub/policy/

# Verify migration applies
python -c "from src.shared.migrations import run_migrations; ..."
```

## 9. Risks and Assumptions

### Risks

1. **Health check timeout**: Nodes that don't respond will be marked unhealthy - this is correct fail-closed behavior
2. **Clock skew**: Health staleness uses UTC time - assumes nodes and hub have reasonable clock sync
3. **Migration ordering**: Must ensure migrations run before health service tries to update health columns

### Assumptions

1. Node agents will expose a `/health` endpoint (CORE-003 will implement this)
2. HTTP connectivity to nodes is available via Tailscale (CORE-004)
3. The hub has an async HTTP client available for health checks

## 10. Blocker Decisions

No blocking decisions required. All architectural choices are resolved:

- Health check protocol: HTTP GET to `/health` endpoint
- Storage: Extended nodes table with health columns
- Policy integration: Via NodePolicy class that can be injected into CORE-005
