# Implementation Summary: LLM-001 - chat_llm base routing and service registry integration

## Ticket Details
- **ID**: LLM-001
- **Title**: chat_llm base routing and service registry integration
- **Wave**: 2
- **Lane**: llm-routing
- **Status**: implementation

## Summary
Implemented the core `chat_llm` routing path so the hub can validate aliases and dispatch prompts to approved backends. The implementation integrates with the existing LLMServicePolicy from CORE-002 and the policy-aware routing framework from CORE-006.

## Changes Made

### New Files Created

| File | Purpose |
|------|---------|
| `src/hub/tools/llm.py` | chat_llm handler implementation |
| `src/hub/services/llm_client.py` | LLM HTTP client for direct service calls |

### Modified Files

| File | Modification |
|------|--------------|
| `src/shared/schemas.py` | Added ChatLLMRequest and ChatLLMResponse schemas |
| `src/hub/tools/__init__.py` | Added register_llm_tools() and registered chat_llm tool |
| `src/hub/dependencies.py` | Added get_llm_service_client() dependency and updated get_policy_aware_router() |
| `src/hub/tool_routing/policy_router.py` | Added llm_service_policy and llm_client parameters to PolicyAwareToolRouter |
| `src/hub/config.py` | Added llm_client_timeout configuration field |

## Acceptance Criteria Verification

| # | Criterion | Status | Implementation |
|---|-----------|--------|----------------|
| 1 | Service aliases are validated before use | ✅ | LLMServicePolicy.validate_service_access() called before routing in chat_llm_impl() |
| 2 | Hub-to-service routing path is explicit | ✅ | LLMServiceClient handles direct HTTP calls; extensible to node-agent routing |
| 3 | Structured latency and outcome metadata are planned | ✅ | Response includes latency_ms, tokens_used, model, finish_reason, success status |

## Implementation Details

### chat_llm Tool
- Validates service_id or service_name against LLMServiceRegistry using LLMServicePolicy
- Supports local and remote service routing (currently direct HTTP, extensible to node-agent)
- Returns structured response with latency_ms, tokens_used, model, finish_reason

### LLMServiceClient
- Handles HTTP communication with LLM services
- Supports different payload formats for llama.cpp, OpenCode, and helper models
- Handles OpenAI-compatible and llama.cpp response formats
- Uses configurable timeout from HubConfig

### Policy Integration
- Uses LLM_REQUIREMENT policy requirement from requirements.py
- Policy validation happens before handler execution via PolicyAwareToolRouter
- Handler receives llm_service_policy and llm_client via dependency injection

## Validation
- All ruff checks pass
- All ruff format checks pass
- Code follows existing patterns in the codebase

## Dependencies
- CORE-002 (LLM service registry) - provides LLMServicePolicy and LLMServiceRepository
- CORE-004 (Hub-to-node client) - provides HTTP client infrastructure
- CORE-006 (MCP tool routing) - provides PolicyAwareToolRouter framework
