# Planning Artifact: SCHED-002

**Ticket:** SCHED-002  
**Title:** Distributed scheduler, node selection, and fallback  
**Stage:** Planning  
**Lane:** scheduler  
**Wave:** 4  

## Summary

Implement the distributed scheduler that considers task type, node health, service availability, and fallback rules. This extends the task classification and routing from SCHED-001 to include node-level awareness — selecting not just which service type, but which node to route to based on health, latency, and capability.

## Dependencies

- **SCHED-001**: Task classification and routing policy (provides TaskRoutingPolicy, TaskClass, service selection)
- **CORE-004**: Hub-to-node client, auth, and health polling (provides HubNodeClient, NodeHealthService, health metadata)
- **LLM-002**: OpenCode adapter and session-aware coding-agent routing (provides OpenCodeAdapter, SessionStore)

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Scheduler inputs are explicit | All decision inputs documented and modeled |
| 2 | Node/backend health affect routing | Unhealthy nodes excluded from selection |
| 3 | Fallback behavior defined and bounded | Explicit fallback chain with max attempts |

## Scope

### In Scope

1. **DistributedScheduler class** — Main orchestrator for node-aware service selection
2. **SchedulerInput model** — All inputs required for scheduling decisions
3. **NodeHealth integration** — Query node health status during selection
4. **Service + node pairing** — Consider both service type and node location
5. **Fallback behavior** — Explicit fallback chain with bounded retries
6. **Latency-aware selection** — Prefer nodes with lower latency
7. **Integration with existing TaskRoutingPolicy** — Extend, don't replace

### Out of Scope

- Cost-based routing optimization
- Load balancing across nodes
- Rate limiting or quota management
- Multi-tenant scheduling

## Technical Design

### 1. Scheduler Inputs Model

Define a new `SchedulerInput` model that captures all decision factors:

```python
from pydantic import BaseModel, Field
from src.shared.models import TaskClass

class SchedulerInput(BaseModel):
    """All inputs required for distributed scheduling decision."""
    
    # Task classification (from SCHED-001)
    task_class: TaskClass = Field(..., description="Task type for routing")
    
    # Service preferences
    preferred_service_id: str | None = Field(None, description="Explicit service ID")
    preferred_service_type: LLMServiceType | None = Field(None, description="Explicit service type")
    
    # Node preferences
    preferred_node_id: str | None = Field(None, description="Explicit node ID")
    exclude_node_ids: list[str] = Field(default_factory=list, description="Nodes to exclude")
    
    # Capability requirements
    required_capabilities: list[str] = Field(default_factory=list, description="Required service capabilities")
    
    # Scheduling constraints
    max_latency_ms: int | None = Field(None, description="Maximum acceptable node latency")
    allow_fallback: bool = Field(True, description="Whether to fallback on failure")
    max_fallback_attempts: int = Field(3, ge=1, le=10, description="Max fallback attempts")
    
    # Context
    trace_id: str | None = Field(None, description="Trace ID for logging")
```

### 2. Scheduler Result Model

```python
class SchedulerResult(BaseModel):
    """Result of a scheduling decision."""
    
    selected_service: LLMServiceInfo = Field(..., description="Selected service")
    selected_node: NodeInfo = Field(..., description="Node hosting the service")
    node_health: NodeHealth | None = Field(None, description="Node health status")
    fallback_chain: list[SchedulerResult] = Field(default_factory=list, description="Ordered fallback options")
    selection_reason: str = Field(..., description="Human-readable selection reason")
    latency_ms: int | None = Field(None, description="Expected latency")
```

### 3. DistributedScheduler Class

```python
class DistributedScheduler:
    """Distributed scheduler with node-aware service selection.
    
    This scheduler extends TaskRoutingPolicy with node-level awareness,
    considering health, latency, and node capabilities during selection.
    """
    
    def __init__(
        self,
        task_routing_policy: TaskRoutingPolicy,
        node_health_service: NodeHealthService,
        node_repository: NodeRepository,
        llm_service_policy: LLMServicePolicy,
    ):
        """Initialize the distributed scheduler.
        
        Args:
            task_routing_policy: Task-based routing from SCHED-001
            node_health_service: Health polling service from CORE-004
            node_repository: Node registry access
            llm_service_policy: Service validation and listing
        """
        self._task_routing = task_routing_policy
        self._health_service = node_health_service
        self._node_repo = node_repository
        self._llm_policy = llm_service_policy
    
    async def schedule(self, input: SchedulerInput) -> SchedulerResult:
        """Make a scheduling decision based on inputs.
        
        Args:
            input: All scheduling inputs
            
        Returns:
            Scheduling result with selected service/node
        """
        # Step 1: Get candidate services from task routing
        candidates = await self._task_routing.get_fallback_chain()
        
        # Step 2: Enrich candidates with node information
        enriched = await self._enrich_with_node_info(candidates, input)
        
        # Step 3: Filter by health and constraints
        filtered = self._filter_by_health(enriched, input)
        
        # Step 4: Select best candidate
        selected = self._select_best(filtered, input)
        
        # Step 5: Build fallback chain
        fallback_chain = self._build_fallback_chain(filtered, selected, input)
        
        return SchedulerResult(
            selected_service=selected.service,
            selected_node=selected.node,
            node_health=selected.health,
            fallback_chain=fallback_chain,
            selection_reason=selected.reason,
            latency_ms=selected.health.health_latency_ms if selected.health else None,
        )
    
    async def _enrich_with_node_info(
        self,
        services: list[LLMServiceInfo],
        input: SchedulerInput,
    ) -> list[ServiceNodePair]:
        """Enrich services with node information."""
        # For each service, find which node hosts it
        # A service can be hosted on multiple nodes (replicated)
        # For now, services are node-specific via their endpoint
        ...
    
    def _filter_by_health(
        self,
        candidates: list[ServiceNodePair],
        input: SchedulerInput,
    ) -> list[ServiceNodePair]:
        """Filter candidates by health status and constraints."""
        # Exclude unhealthy nodes
        # Exclude excluded_node_ids
        # Filter by max_latency_ms if specified
        ...
    
    def _select_best(
        self,
        candidates: list[ServiceNodePair],
        input: SchedulerInput,
    ) -> ServiceNodePair:
        """Select best candidate from filtered list."""
        # Prefer lowest latency
        # If tie, prefer healthier node
        # If tie, pick first
        ...
    
    def _build_fallback_chain(
        self,
        candidates: list[ServiceNodePair],
        selected: ServiceNodePair,
        input: SchedulerInput,
    ) -> list[SchedulerResult]:
        """Build ordered fallback chain."""
        # Return remaining candidates as fallback options
        ...
```

### 4. Health-Aware Service Selection

Integration with `NodeHealthService` from CORE-004:

```python
async def get_node_health_for_service(
    service: LLMServiceInfo,
) -> NodeHealth | None:
    """Get health status for node hosting a service.
    
    Services are associated with nodes via:
    1. Direct node_id field in service metadata
    2. Node hostname extracted from service endpoint
    
    This needs extension to LLMServiceInfo or service repository.
    """
    # Query node_health_service.get_node_health(node_id)
    # Return health status
```

### 5. Fallback Behavior

| Scenario | Behavior |
|----------|----------|
| Selected node unhealthy | Filter out, select next best |
| Selected node goes offline during request | Fallback to next in chain |
| All nodes for task type unhealthy | Fallback to any available service |
| Node latency exceeds max_latency_ms | Filter out or warn |
| All fallbacks exhausted | Return aggregate error |

**Fallback Chain Rules:**
- Maximum fallback attempts bounded by `max_fallback_attempts` (default 3)
- Each fallback logs: `trace_id`, `from_node`, `to_node`, `reason`
- Fallback only proceeds if `allow_fallback=True`
- Do NOT fallback on auth failures (fail closed)

### 6. Integration with Existing Tools

Update existing tool handlers to use the new scheduler:

```python
# In src/hub/tools/llm.py
async def chat_llm_handler(
    ...
    scheduler_input: SchedulerInput | None = None,
    distributed_scheduler: DistributedScheduler | None = None,
) -> dict[str, Any]:
    """Handle chat_llm with distributed scheduling."""
    
    # If scheduler_input provided, use distributed scheduler
    if scheduler_input and distributed_scheduler:
        result = await distributed_scheduler.schedule(scheduler_input)
        # Use result.selected_service and result.selected_node
    else:
        # Fall back to existing TaskRoutingPolicy behavior
        ...
```

## Implementation Steps

### Step 1: Add Scheduler Models

**File:** `src/shared/models.py`

Add:
- `SchedulerInput` model
- `SchedulerResult` model  
- `ServiceNodePair` helper class

### Step 2: Create DistributedScheduler

**File:** `src/hub/policy/distributed_scheduler.py`

Create:
- `DistributedScheduler` class
- Helper methods for health filtering and selection

### Step 3: Add Node-Service Association

**File:** `src/shared/repositories/llm_services.py` (or new method)

Add method to query which nodes host which services. This requires:
- Either extending `LLMServiceInfo` with `node_id` field
- Or maintaining a mapping in the service repository

### Step 4: Add DI Provider

**File:** `src/hub/dependencies.py`

Add:
- `get_distributed_scheduler()` provider

### Step 5: Update LLM Tools

**Files:**
- `src/hub/tools/llm.py`
- `src/hub/tools/opencode.py`
- `src/hub/tools/embedding.py`

Update each to accept optional `SchedulerInput` and use `DistributedScheduler` when provided.

### Step 6: Export Models

**File:** `src/shared/__init__.py`

Export new models.

## Files to Create

1. `src/hub/policy/distributed_scheduler.py` — Main distributed scheduler class

## Files to Modify

1. `src/shared/models.py` — Add SchedulerInput, SchedulerResult models
2. `src/shared/__init__.py` — Export new models
3. `src/hub/dependencies.py` — Add DI provider for DistributedScheduler
4. `src/hub/tools/llm.py` — Integrate distributed scheduler
5. `src/hub/tools/opencode.py` — Integrate distributed scheduler
6. `src/hub/tools/embedding.py` — Integrate distributed scheduler

## Integration Points

| Component | Integration |
|-----------|-------------|
| TaskRoutingPolicy (SCHED-001) | Extended for node-aware selection |
| NodeHealthService (CORE-004) | Query health status during selection |
| NodeRepository | List nodes and their status |
| LLMServicePolicy | Validate and list services |
| HubNodeClient | Execute on selected node |

## Validation Plan

1. **Static Analysis:**
   - Run `ruff check src/hub/policy/distributed_scheduler.py`
   - Verify type hints complete

2. **Unit Tests:**
   - Test `SchedulerInput` validation
   - Test `DistributedScheduler.schedule()` with various inputs
   - Test health filtering excludes unhealthy nodes
   - Test fallback chain construction
   - Test latency filtering

3. **Integration Tests:**
   - Test scheduler with mock health service
   - Test fallback when primary node unavailable
   - Test integration with chat_llm tool

4. **Code Inspection:**
   - Verify all scheduler inputs are explicit
   - Verify unhealthy nodes filtered
   - Verify fallback bounded by max_fallback_attempts

## Risks and Assumptions

| Risk | Mitigation |
|------|------------|
| Service-to-node mapping not explicit | Add node_id to LLMServiceInfo or maintain mapping |
| Health check staleness | Use is_stale property from NodeHealth |
| Circular fallback loops | Fallback chain is a list, never recurses |
| Node becomes unhealthy mid-request | Handle at tool execution layer with retry |

## Decision Blockers

None — all blocking decisions resolved:
- Task classification from SCHED-001 provides TaskClass
- Node health from CORE-004 provides NodeHealthService
- Service routing from SCHED-001 provides TaskRoutingPolicy

## Open Questions (Non-Blocking)

1. **How are services associated with nodes?** — Can store node_id in LLMServiceInfo metadata or maintain separate mapping
2. **Should fallback include different service types?** — Yes, fallback chain includes all candidates sorted by preference
3. **How to handle replicated services?** — Take first available healthy node; can extend to round-robin later

## Acceptance Signal

After implementation, calling LLM tools with explicit `SchedulerInput` will route to the appropriate node based on:
1. Task classification (from SCHED-001)
2. Node health status (from CORE-004)
3. Latency preferences
4. Explicit node/service preferences

And failures will trigger bounded fallback to the next healthy node in the chain.
