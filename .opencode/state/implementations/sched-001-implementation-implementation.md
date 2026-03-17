# Implementation Artifact: SCHED-001

**Ticket:** SCHED-001  
**Title:** Task classification and routing policy  
**Stage:** Implementation  
**Lane:** scheduler  
**Wave:** 4  

## Summary

Implemented task classification and routing policy for GPTTalker LLM service selection. The implementation defines task classes, service capability metadata, and a routing policy that uses registered backend metadata to select appropriate services with fallback behavior.

## Changes Made

### 1. New Files Created

- **`src/hub/policy/task_routing_policy.py`**: Main routing policy implementation
  - `TASK_CLASS_MAPPING`: Default mapping from TaskClass to LLMServiceType
  - `TaskRoutingPolicy`: Class for selecting services based on task classification
  - `TaskRoutingError`: Exception for routing failures with details
  - `should_fallback()`: Method to determine if error warrants fallback

### 2. Modified Files

- **`src/shared/models.py`**: Added new models
  - `TaskClass`: StrEnum with 6 categories (coding, chat, embedding, summarize, reasoning, search)
  - `TaskClassification`: Model with task_class, confidence, and reasoning
  - `ServiceCapabilities`: Model for service capability metadata

- **`src/hub/dependencies.py`**: Added DI provider
  - `get_task_routing_policy()`: Dependency provider for TaskRoutingPolicy
  - Added `TaskClass` and `TaskRoutingPolicy` imports

- **`src/hub/tools/llm.py`**: Enhanced with task routing
  - Added `task_class` parameter to `chat_llm_handler`
  - Added `chat_llm_with_routing()`: Implementation using fallback chain
  - Added `task_routing_policy` dependency injection

- **`src/hub/tools/opencode.py`**: Enhanced with task routing
  - Added `task_class` parameter to `chat_opencode_handler`
  - Added `chat_opencode_with_routing()`: Implementation using fallback chain
  - Added `task_routing_policy` dependency injection

- **`src/hub/tools/embedding.py`**: Enhanced with task routing
  - Added `task_class` parameter to `ChatEmbeddingsParams`
  - Added `chat_embeddings_with_routing()`: Implementation for auto-routing
  - Refactored to use separate `do_embedding_request()` helper

## Acceptance Criteria Verification

| # | Criterion | Status | Verification |
|---|-----------|--------|--------------|
| 1 | Task classes are explicit | ✅ PASS | TaskClass enum defines 6 categories with documentation |
| 2 | Routing policy uses registered backend metadata | ✅ PASS | Route decision uses LLMServiceInfo from registry, gets service list via LLMServicePolicy |
| 3 | Fallback expectations are defined | ✅ PASS | Policy specifies fallback behavior: availability errors (404, 503, timeout, connection) trigger fallback; auth failures do NOT fallback; all failures tracked with attempted_services and errors |

## Fallback Behavior

| Scenario | Behavior |
|----------|----------|
| Primary service unavailable (404/503) | Try next service in fallback chain |
| Primary service timeout | Try next service, log timeout error |
| Primary service auth failure | Do NOT fallback — fail closed |
| All services failed | Return aggregate error with all failure reasons |
| No fallback configured | Return single error immediately |

## Routing Chain Example

When `task_class=chat` is specified without explicit service:
1. Query registry for services of type LLAMA
2. If none, query for HELPER type
3. If none, use any available service
4. Try each until success or all fail

## Files Modified Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| src/shared/models.py | +38 | Add TaskClass, TaskClassification, ServiceCapabilities |
| src/hub/policy/task_routing_policy.py | +191 | New routing policy implementation |
| src/hub/dependencies.py | +18 | Add DI provider |
| src/hub/tools/llm.py | +89 | Add task routing support |
| src/hub/tools/opencode.py | +103 | Add task routing support |
| src/hub/tools/embedding.py | +87 | Add task routing support |

## Validation

- ✅ Ruff lint passes on all modified files
- ✅ No import errors
- ✅ Type hints complete

## Next Steps

The routing policy is now available for use by the LLM tools. Future tickets can extend this with:
- Auto-detection of task class from prompt content (SCHED-002)
- Health-aware scheduling beyond basic availability
- Cost-based routing optimization
