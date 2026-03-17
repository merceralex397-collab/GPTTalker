# Planning Artifact: SCHED-001

**Ticket:** SCHED-001  
**Title:** Task classification and routing policy  
**Stage:** Planning  
**Lane:** scheduler  
**Wave:** 4  

## Summary

Define how GPTTalker classifies task types and selects between approved LLM and execution backends. This ticket establishes the routing policy layer that sits between the MCP tool interface (chat_llm, chat_opencode, chat_embeddings) and the actual LLM service clients.

## Dependencies

- **CORE-002**: Repo, write-target, and LLM service registries (provides LLMServiceInfo model and policy)
- **LLM-001**: chat_llm base routing and service registry integration (provides LLMServiceClient)

## Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Task classes are explicit | Enum or model defines all task types with documentation |
| 2 | Routing policy uses registered backend metadata | Route decision uses LLMServiceInfo (type, endpoint, capabilities) |
| 3 | Fallback expectations are defined | Policy specifies fallback behavior, ordering, and failure modes |

## Scope

### In Scope

1. **Task classification model** — Define TaskClass enum with categories
2. **Task-to-service mapping policy** — Define how task classes map to service types
3. **Routing policy engine** — Create TaskRoutingPolicy class that selects backends
4. **Fallback configuration** — Define fallback chain and retry expectations
5. **Integration with existing LLM tools** — Wire routing into chat_llm, chat_opencode, chat_embeddings

### Out of Scope

- Distributed node selection (SCHED-002)
- Health-aware scheduling beyond basic availability
- Cost-based routing optimization
- Rate limiting or quota management

## Technical Design

### 1. Task Classification Model

Define a new `TaskClass` enum in `src/shared/models.py`:

```python
class TaskClass(StrEnum):
    CODING = "coding"           # Code generation, editing, review
    CHAT = "chat"               # General conversation
    EMBEDDING = "embedding"     # Text vectorization
    SUMMARIZATION = "summarize" # Document summarization
    REASONING = "reasoning"     # Complex reasoning workloads
    SEARCH = "search"           # Semantic search queries
```

Add a `TaskClassification` model:

```python
class TaskClassification(BaseModel):
    task_class: TaskClass
    confidence: float = 1.0  # For future ML-based classification
    reasoning: str | None = None  # Why this classification was chosen
```

### 2. Service Capability Metadata

Extend `LLMServiceInfo` with optional capabilities (or use metadata JSON field):

```python
class ServiceCapabilities(BaseModel):
    supports_streaming: bool = False
    max_tokens: int | None = None
    context_window: int | None = None
    recommended_for: list[TaskClass] = []
```

The routing policy will query `ServiceCapabilities` from the service's metadata to inform routing decisions.

### 3. Task-to-Service Mapping

Define default mapping in a new policy file `src/hub/policy/task_routing_policy.py`:

```python
TASK_CLASS_MAPPING: dict[TaskClass, list[LLMServiceType]] = {
    TaskClass.CODING: [LLMServiceType.OPENCODE, LLMServiceType.LLAMA],
    TaskClass.CHAT: [LLMServiceType.LLAMA, LLMServiceType.HELPER],
    TaskClass.EMBEDDING: [LLMServiceType.EMBEDDING],
    TaskClass.SUMMARIZATION: [LLMServiceType.LLAMA, LLMServiceType.HELPER],
    TaskClass.REASONING: [LLMServiceType.LLAMA],
    TaskClass.SEARCH: [LLMTaskClass.EMBEDDING],  # For query embedding
}
```

This mapping is configurable via the service registry metadata.

### 4. TaskRoutingPolicy Class

```python
class TaskRoutingPolicy:
    def __init__(
        self,
        llm_service_policy: LLMServicePolicy,
        task_class: TaskClass,
        preferred_service_id: str | None = None,
    ):
        ...

    def select_service(self) -> LLMServiceInfo:
        """Select the best service for the task class."""
        ...

    def get_fallback_chain(self) -> list[LLMServiceInfo]:
        """Get ordered fallback services."""
        ...

    def should_fallback(self, error: Exception) -> bool:
        """Determine if error warrants fallback."""
        ...
```

### 5. Fallback Expectations

| Scenario | Behavior |
|----------|----------|
| Primary service unavailable (404/503) | Try next service in fallback chain |
| Primary service timeout | Try next service, log timeout error |
| Primary service auth failure | Do NOT fallback — fail closed (config error) |
| All services failed | Return aggregate error with all failure reasons |
| No fallback configured | Return single error immediately |

**Retry expectations:**
- No automatic retry within a single service attempt
- Fallback chain is traversed in order
- Each fallback attempt logs trace_id, service_id, latency_ms

## Implementation Steps

### Step 1: Add TaskClass to models.py

**File:** `src/shared/models.py`

Add:
- `TaskClass` StrEnum
- `TaskClassification` model  
- `ServiceCapabilities` model

### Step 2: Create TaskRoutingPolicy

**File:** `src/hub/policy/task_routing_policy.py`

Create:
- `TASK_CLASS_MAPPING` dict
- `TaskRoutingPolicy` class with select_service(), get_fallback_chain(), should_fallback()

### Step 3: Add DI Provider

**File:** `src/hub/dependencies.py`

Add:
- `get_task_routing_policy()` provider

### Step 4: Update LLM Tools

**Files:** 
- `src/hub/tools/llm.py`
- `src/hub/tools/opencode.py`
- `src/hub/tools/embeddings.py`

Update each tool handler to:
1. Accept optional `task_class` parameter
2. Use `TaskRoutingPolicy` to select service if not explicitly specified
3. Apply fallback chain on failures

### Step 5: Register Tools (if new parameters added)

**File:** `src/hub/tools/__init__.py`

If new tool parameters are added to MCP tool schemas, update registrations.

### Step 6: Export New Models

**File:** `src/shared/__init__.py`

Export new models for import convenience.

## Integration Points

| Component | Integration |
|-----------|-------------|
| LLMServicePolicy | Used to validate and list services |
| LLMServiceClient | Used to execute chat after routing |
| chat_llm tool | Updated to use routing policy |
| chat_opencode tool | Updated to use routing policy |
| chat_embeddings tool | Updated to use routing policy |

## Files to Create

1. `src/hub/policy/task_routing_policy.py` — Main routing policy class

## Files to Modify

1. `src/shared/models.py` — Add TaskClass, TaskClassification, ServiceCapabilities
2. `src/shared/__init__.py` — Export new models
3. `src/hub/dependencies.py` — Add DI provider for TaskRoutingPolicy
4. `src/hub/tools/llm.py` — Integrate routing policy
5. `src/hub/tools/opencode.py` — Integrate routing policy
6. `src/hub/tools/embeddings.py` — Integrate routing policy

## Validation Plan

1. **Static Analysis:**
   - Run `ruff check src/hub/policy/task_routing_policy.py`
   - Run `ruff check src/shared/models.py`
   - Verify type hints complete

2. **Unit Tests:**
   - Test `TaskClass` enum values
   - Test `TaskRoutingPolicy.select_service()` with various task classes
   - Test `TaskRoutingPolicy.get_fallback_chain()` returns correct order
   - Test `should_fallback()` for different error types

3. **Integration Tests:**
   - Test routing from chat_llm tool with explicit task_class
   - Test fallback behavior when primary service unavailable

4. **Code Inspection:**
   - Verify routing uses LLMServiceInfo metadata (not hardcoded)
   - Verify fallback chain respects TASK_CLASS_MAPPING

## Risks and Assumptions

| Risk | Mitigation |
|------|------------|
| Task classification is user-specified (not auto-detected) | Accept explicit task_class parameter; default to CHAT if not provided |
| Service capabilities not populated in DB | Routing falls back to TASK_CLASS_MAPPING defaults |
| Circular fallback loops | Fallback chain is a list, never recurses |

## Decision Blockers

None — all blocking decisions resolved:

- Task class enum values defined above
- Routing uses existing LLMServiceInfo metadata
- Fallback behavior specified

## Open Questions (Non-Blocking)

1. **Should task_class be auto-detected?** — Not in scope; can be added in SCHED-002
2. **Should capabilities be required?** — Optional; defaults provided in mapping
3. **Should fallback be configurable per-service?** — Can be stored in metadata JSON

## Acceptance Signal

After implementation, calling `chat_llm` with an explicit `task_class` parameter will route to the appropriate service type based on the policy, and failures will trigger fallback to the next available service in the chain.
