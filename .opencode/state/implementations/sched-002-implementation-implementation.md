# Implementation Artifact: SCHED-002

**Ticket:** SCHED-002  
**Title:** Distributed scheduler, node selection, and fallback  
**Stage:** Implementation  
**Lane:** scheduler  
**Wave:** 4  

## Summary

Implemented the distributed scheduler that considers task type, node health, service availability, and fallback rules. This extends the task classification and routing from SCHED-001 to include node-level awareness — selecting not just which service type, but which node to route to based on health, latency, and capability.

## Changes Made

### 1. New Files Created

- **`src/hub/policy/distributed_scheduler.py`** — Main distributed scheduler class with:
  - `SchedulerInput` model (in models.py) — All decision inputs for scheduling
  - `SchedulerResult` model (in models.py) — Scheduling decision result
  - `NodeHealthInfo` model (in models.py) — Compact health info for scheduling
  - `ServiceNodePair` helper class (in models.py) — Service-node pairing
  - `DistributedScheduler` class — Main orchestrator for node-aware selection
  - `DistributedSchedulerError` exception — Error handling

### 2. Modified Files

- **`src/shared/models.py`**
  - Added `SchedulerInput` model with task class, service/node preferences, constraints
  - Added `SchedulerResult` model with selected service/node, health, fallback chain
  - Added `NodeHealthInfo` model for compact health data
  - Added `ServiceNodePair` helper class for candidate representation

- **`src/hub/dependencies.py`**
  - Added `get_distributed_scheduler()` DI provider

- **`src/hub/tools/llm.py`**
  - Added optional `scheduler_input` and `distributed_scheduler` parameters
  - Added `chat_llm_with_distributed_scheduler()` function
  - Added `_try_fallback_chain()` helper for fallback handling

- **`src/hub/tools/opencode.py`**
  - Added optional `scheduler_input` and `distributed_scheduler` parameters
  - Added `chat_opencode_with_distributed_scheduler()` function
  - Added `_opencode_try_fallback_chain()` helper for fallback handling

- **`src/hub/tools/embedding.py`**
  - Added `scheduler_input` field to `ChatEmbeddingsParams`
  - Added optional `distributed_scheduler` parameter to handler
  - Added `chat_embeddings_with_distributed_scheduler()` function
  - Added `_embedding_try_fallback_chain()` helper

## Key Features Implemented

### 1. Scheduler Inputs Explicit

All decision inputs are modeled in `SchedulerInput`:
- `task_class`: Task type for routing (CODING, CHAT, EMBEDDING, etc.)
- `preferred_service_id`: Explicit service to use
- `preferred_service_type`: Explicit service type preference
- `preferred_node_id`: Explicit node to prefer
- `exclude_node_ids`: Nodes to exclude
- `required_capabilities`: Required service capabilities
- `max_latency_ms`: Maximum acceptable latency
- `allow_fallback`: Whether to fallback on failure
- `max_fallback_attempts`: Maximum fallback attempts (1-10)
- `trace_id`: For logging

### 2. Node/Backend Health Affect Routing

- Health filtering via `_filter_by_health()` method
- Unhealthy nodes (health_status != HEALTHY) are excluded from selection
- Nodes with latency exceeding `max_latency_ms` are filtered out
- Unknown health status is treated as not healthy (fail-closed)
- Latency-aware selection prefers lower-latency nodes

### 3. Fallback Behavior Defined and Bounded

- Maximum fallback attempts bounded by `max_fallback_attempts` (default 3, max 10)
- Fallback chain built from remaining healthy candidates
- Fallback only proceeds if `allow_fallback=True`
- Do NOT fallback on auth failures (fail closed)
- Each fallback logs trace_id, from_node, to_node, reason

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Scheduler inputs explicit | ✅ | All inputs modeled in `SchedulerInput` |
| Node/backend health affect routing | ✅ | `_filter_by_health()` excludes unhealthy nodes |
| Fallback behavior defined and bounded | ✅ | `max_fallback_attempts` bounds retries |

## Integration Points

| Component | Integration |
|-----------|-------------|
| TaskRoutingPolicy (SCHED-001) | Extended for node-aware selection |
| NodeHealthService (CORE-004) | Query health status during selection |
| NodeRepository | List nodes and their status |
| LLMServicePolicy | Validate and list services |
| HubNodeClient | Execute on selected node |

## Validation

- All new models added to models.py with proper Pydantic validation
- DistributedScheduler class implements full scheduling workflow
- DI provider added for easy injection
- Tool handlers updated to optionally use distributed scheduling

## Notes

- Services without explicit node association are treated as node-agnostic
- Health data staleness is checked via `is_stale` property
- Fail-closed behavior: unknown health means not healthy
- Fallback chain is ordered by latency and health priority
