# Implementation Plan: LLM-001 - chat_llm base routing and service registry integration

## Ticket Overview

- **ID**: LLM-001
- **Title**: chat_llm base routing and service registry integration
- **Wave**: 2
- **Lane**: llm-routing
- **Summary**: Implement the core `chat_llm` routing path so the hub can validate aliases and dispatch prompts to approved backends.
- **Dependencies**: CORE-002 (done), CORE-004 (done), CORE-006 (done)

## Acceptance Criteria

| # | Criterion | Verification Approach |
|---|-----------|---------------------|
| 1 | Service aliases are validated before use | LLMServicePolicy.validate_service_access() called before routing |
| 2 | Hub-to-service routing path is explicit | Different routing logic for local vs remote services |
| 3 | Structured latency and outcome metadata are planned | Response includes duration_ms, outcome status, service metadata |

## Implementation Approach

### Architecture Overview

The `chat_llm` tool will:
1. Accept a `service_id` (or `service_name`) parameter to identify the target LLM backend
2. Validate the service against the LLMServiceRegistry using LLMServicePolicy
3. Route the request based on service configuration:
   - **Local service**: Direct HTTP call to the service endpoint
   - **Remote service**: Route through the node agent (if service is hosted on a managed node)
4. Return structured response with latency metadata and outcome status

### Service Types (from LLMServiceType enum)

- `OPENCODE`: OpenCode coding agent service
- `LLAMA`: llama.cpp-compatible local inference
- `EMBEDDING`: Dedicated embedding service
- `HELPER`: Helper-class models

### Routing Strategy

```
chat_llm request
       │
       ▼
┌──────────────────┐
│ Validate service │
│   via Policy    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check endpoint  │
│   configuration │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
Local    Remote
    │         │
    ▼         ▼
Direct    Node
HTTP      Agent
```

## File Structure

### New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/tools/llm.py` | chat_llm handler implementation |
| `src/hub/services/llm_client.py` | LLM service HTTP client for direct calls |

### Existing Files to Modify

| File | Modification |
|------|--------------|
| `src/shared/schemas.py` | Add ChatLLMRequest, ChatLLMResponse schemas |
| `src/hub/tools/__init__.py` | Register chat_llm tool |
| `src/hub/dependencies.py` | Add llm_service_policy dependency injection to router |
| `src/hub/tool_routing/policy_router.py` | Add llm_service_policy parameter to PolicyAwareToolRouter |

## Detailed Implementation Steps

### Step 1: Add Request/Response Schemas

**File**: `src/shared/schemas.py`

Add new schema classes:

```python
class ChatLLMRequest(BaseModel):
    """Request model for chat_llm tool."""
    service_id: str | None = Field(None, description="LLM service identifier")
    service_name: str | None = Field(None, description="LLM service name (alternative to service_id)")
    prompt: str = Field(..., description="Prompt to send to LLM")
    max_tokens: int = Field(1000, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Sampling temperature")
    session_id: str | None = Field(None, description="Optional session ID for conversation continuity")
    system_prompt: str | None = Field(None, description="Optional system prompt")


class ChatLLMResponse(BaseModel):
    """Response model for chat_llm tool."""
    success: bool = Field(..., description="Whether the request succeeded")
    response: str | None = Field(None, description="LLM response text")
    model: str | None = Field(None, description="Model that generated the response")
    service_id: str = Field(..., description="Service ID that handled the request")
    service_name: str | None = Field(None, description="Human-readable service name")
    latency_ms: int = Field(..., description="Request latency in milliseconds")
    tokens_used: int | None = Field(None, description="Total tokens used")
    finish_reason: str | None = Field(None, description="Reason for completion")
    error: str | None = Field(None, description="Error message if failed")
```

### Step 2: Create LLM Service HTTP Client

**File**: `src/hub/services/llm_client.py`

This client handles direct HTTP calls to LLM services (when they're accessible directly, not through node agents).

```python
"""HTTP client for direct LLM service communication."""

import httpx
from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo

logger = get_logger(__name__)


class LLMServiceClient:
    """HTTP client for communicating with LLM services.
    
    This client is used when LLM services are accessible directly
    (e.g., local llama.cpp server, remote API endpoints).
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        default_timeout: float = 120.0,
    ):
        """Initialize the LLM service client.
        
        Args:
            http_client: The underlying async HTTP client.
            default_timeout: Default request timeout in seconds.
        """
        self._client = http_client
        self._default_timeout = default_timeout

    async def chat(
        self,
        service: LLMServiceInfo,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a chat request to an LLM service.
        
        Args:
            service: LLM service configuration.
            prompt: User prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            session_id: Optional session ID.
            
        Returns:
            Dictionary with response text and metadata.
        """
        # Build request payload based on service type
        if service.type == LLMServiceType.LLAMA:
            payload = self._build_llama_payload(prompt, max_tokens, temperature, system_prompt)
        elif service.type == LLMServiceType.OPENCODE:
            payload = self._build_opencode_payload(prompt, max_tokens, temperature, system_prompt, session_id)
        elif service.type == LLMServiceType.HELPER:
            payload = self._build_helper_payload(prompt, max_tokens, temperature, system_prompt)
        else:
            raise ValueError(f"Unsupported service type: {service.type}")

        # Make the request
        response = await self._client.post(
            service.endpoint,
            json=payload,
            timeout=self._default_timeout,
            headers={"Authorization": f"Bearer {service.api_key}"} if service.api_key else {},
        )

        response.raise_for_status()
        return self._parse_response(response.json(), service)

    def _build_llama_payload(self, prompt: str, max_tokens: int, temperature: float, system_prompt: str | None) -> dict:
        """Build payload for llama.cpp-compatible API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

    def _build_opencode_payload(self, prompt: str, max_tokens: int, temperature: float, system_prompt: str | None, session_id: str | None) -> dict:
        """Build payload for OpenCode API."""
        # OpenCode-specific format
        return {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "session_id": session_id,
        }

    def _build_helper_payload(self, prompt: str, max_tokens: int, temperature: float, system_prompt: str | None) -> dict:
        """Build payload for helper model API."""
        return {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system_prompt": system_prompt,
        }

    def _parse_response(self, response: dict, service: LLMServiceInfo) -> dict:
        """Parse LLM service response into standardized format."""
        # Handle different response formats
        if "choices" in response:  # OpenAI-compatible
            choice = response["choices"][0]
            return {
                "response": choice.get("message", {}).get("content", ""),
                "model": response.get("model", service.name),
                "tokens_used": response.get("usage", {}).get("total_tokens"),
                "finish_reason": choice.get("finish_reason"),
            }
        elif "response" in response:  # llama.cpp format
            return {
                "response": response["response"],
                "model": response.get("model", service.name),
                "tokens_used": response.get("tokens_used"),
                "finish_reason": response.get("stop", "length"),
            }
        else:
            # Generic fallback
            return {
                "response": str(response),
                "model": service.name,
                "tokens_used": None,
                "finish_reason": None,
            }
```

### Step 3: Create chat_llm Tool Handler

**File**: `src/hub/tools/llm.py`

```python
"""LLM routing tools for chat_llm."""

import time
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, LLMServiceType

# Type hints for forward references
if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.hub.services.llm_client import LLMServiceClient

logger = get_logger(__name__)


async def chat_llm_handler(
    service_id: str | None = None,
    service_name: str | None = None,
    prompt: str = "",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    system_prompt: str | None = None,
    session_id: str | None = None,
    llm_service_policy: "LLMServicePolicy | None" = None,
    llm_client: "LLMServiceClient | None" = None,
) -> dict[str, Any]:
    """Handle chat_llm tool invocation.
    
    This tool routes LLM requests to approved backends after validating
    the service alias against the registry.
    
    Args:
        service_id: Service identifier (validated against registry).
        service_name: Service name (alternative to service_id).
        prompt: User prompt to send to LLM.
        max_tokens: Maximum tokens in response.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID for conversation continuity.
        llm_service_policy: LLMServicePolicy for service validation.
        llm_client: LLMServiceClient for making HTTP calls.
        
    Returns:
        Dictionary with LLM response and metadata.
    """
    if llm_service_policy is None:
        return {"success": False, "error": "LLMServicePolicy not available"}
    
    if llm_client is None:
        return {"success": False, "error": "LLMServiceClient not available"}
    
    if not service_id and not service_name:
        return {"success": False, "error": "Either service_id or service_name is required"}
    
    if not prompt:
        return {"success": False, "error": "Prompt is required"}
    
    return await chat_llm_impl(
        service_id=service_id,
        service_name=service_name,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt,
        session_id=session_id,
        llm_service_policy=llm_service_policy,
        llm_client=llm_client,
    )


async def chat_llm_impl(
    service_id: str | None,
    service_name: str | None,
    prompt: str,
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    session_id: str | None,
    llm_service_policy: "LLMServicePolicy",
    llm_client: "LLMServiceClient",
) -> dict[str, Any]:
    """Internal implementation for chat_llm.
    
    Args:
        service_id: Service identifier.
        service_name: Service name.
        prompt: User prompt.
        max_tokens: Maximum tokens.
        temperature: Sampling temperature.
        system_prompt: Optional system prompt.
        session_id: Optional session ID.
        llm_service_policy: Policy for validation.
        llm_client: Client for HTTP calls.
        
    Returns:
        Response dictionary with metadata.
    """
    start_time = int(time.time() * 1000)
    
    # Step 1: Validate service access
    service: LLMServiceInfo | None = None
    try:
        if service_id:
            service = await llm_service_policy.validate_service_access(service_id)
        elif service_name:
            service = await llm_service_policy.validate_service_by_name(service_name)
    except ValueError as e:
        logger.warning("llm_service_validation_failed", service_id=service_id, service_name=service_name, error=str(e))
        return {
            "success": False,
            "error": f"Service validation failed: {e}",
            "latency_ms": int(time.time() * 1000) - start_time,
        }
    
    if not service:
        return {
            "success": False,
            "error": "Service not found",
            "latency_ms": int(time.time() * 1000) - start_time,
        }
    
    # Step 2: Check if service has endpoint configured
    if not service.endpoint:
        logger.warning("llm_service_no_endpoint", service_id=service.service_id)
        return {
            "success": False,
            "error": f"Service {service.name} has no endpoint configured",
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": int(time.time() * 1000) - start_time,
        }
    
    # Step 3: Route to service
    # For now, we support direct HTTP calls to services
    # Future: Route through node agent if service is hosted on a managed node
    try:
        result = await llm_client.chat(
            service=service,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
            session_id=session_id,
        )
        
        latency_ms = int(time.time() * 1000) - start_time
        
        logger.info(
            "llm_request_success",
            service_id=service.service_id,
            service_name=service.name,
            latency_ms=latency_ms,
            tokens_used=result.get("tokens_used"),
        )
        
        return {
            "success": True,
            "response": result.get("response"),
            "model": result.get("model"),
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": latency_ms,
            "tokens_used": result.get("tokens_used"),
            "finish_reason": result.get("finish_reason"),
        }
        
    except Exception as e:
        latency_ms = int(time.time() * 1000) - start_time
        logger.error(
            "llm_request_failed",
            service_id=service.service_id,
            service_name=service.name,
            error=str(e),
            latency_ms=latency_ms,
        )
        
        return {
            "success": False,
            "error": f"LLM request failed: {e}",
            "service_id": service.service_id,
            "service_name": service.name,
            "latency_ms": latency_ms,
        }
```

### Step 4: Register chat_llm Tool

**File**: `src/hub/tools/__init__.py`

Add new registration function:

```python
def register_llm_tools(registry: ToolRegistry) -> None:
    """Register LLM routing tools with the tool registry.
    
    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.llm import chat_llm_handler
    from src.hub.tool_routing.requirements import LLM_REQUIREMENT

    # Register chat_llm tool
    # Policy: LLM_REQUIREMENT - requires valid LLM service access
    registry.register(
        ToolDefinition(
            name="chat_llm",
            description="Send a prompt to an approved LLM backend. "
            "Validates the service alias against the registry before routing. "
            "Returns the LLM response along with latency and token metadata. "
            "Supports various LLM backends including OpenCode, llama.cpp, and helper models.",
            handler=chat_llm_handler,
            parameters={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "LLM service identifier from the registry",
                    },
                    "service_name": {
                        "type": "string",
                        "description": "Human-readable service name (alternative to service_id)",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "User prompt to send to the LLM",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "default": 1000,
                        "maximum": 4096,
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 2.0,
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Optional system prompt to set context",
                        "default": None,
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation continuity",
                        "default": None,
                    },
                },
                "required": ["prompt"],
                "oneOf": [
                    {"required": ["service_id"]},
                    {"required": ["service_name"]},
                ],
            },
            policy=LLM_REQUIREMENT,
        )
    )
```

Update `register_all_tools`:

```python
def register_all_tools(registry: ToolRegistry) -> None:
    register_discovery_tools(registry)
    register_inspection_tools(registry)
    register_search_tools(registry)
    register_markdown_tools(registry)
    register_llm_tools(registry)  # NEW
```

### Step 5: Add LLM Service Client to Dependencies

**File**: `src/hub/dependencies.py`

Add dependency provider:

```python
async def get_llm_service_client(
    request: Request,
) -> LLMServiceClient:
    """Get LLM service HTTP client.
    
    Args:
        request: The current FastAPI request.
        
    Returns:
        LLMServiceClient instance.
    """
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Ensure lifespan has run.")
    
    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")
    
    return LLMServiceClient(
        http_client=http_client,
        default_timeout=config.llm_client_timeout,  # Add to HubConfig
    )
```

### Step 6: Update PolicyAwareToolRouter

**File**: `src/hub/tool_routing/policy_router.py`

Add llm_service_policy to constructor:

```python
def __init__(
    self,
    registry: ToolRegistry,
    policy_engine: PolicyEngine,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
    node_client: "HubNodeClient | None" = None,
    write_target_repo: "WriteTargetRepository | None" = None,
    write_target_policy: "WriteTargetPolicy | None" = None,
    llm_service_policy: "LLMServicePolicy | None" = None,  # NEW
):
    # ... existing code ...
    self._llm_service_policy = llm_service_policy
```

Add handler injection for llm_service_policy and llm_client:

```python
async def _execute_handler(
    self,
    handler: Any,
    parameters: dict[str, Any],
    trace_id: str | None,
    log_context: dict[str, Any],
) -> dict[str, Any]:
    # ... existing code ...
    
    # Add llm_service_policy injection
    if self._llm_service_policy is not None:
        sig = inspect.signature(handler)
        if "llm_service_policy" in sig.parameters:
            exec_kwargs["llm_service_policy"] = self._llm_service_policy
    
    # Add llm_client injection
    if self._llm_client is not None:
        sig = inspect.signature(handler)
        if "llm_client" in sig.parameters:
            exec_kwargs["llm_client"] = self._llm_client
```

### Step 7: Update get_policy_aware_router

**File**: `src/hub/dependencies.py`

Update the router dependency to include new parameters:

```python
async def get_policy_aware_router(
    registry: ToolRegistry = Depends(get_tool_registry),
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    node_repo: NodeRepository = Depends(get_node_repository),
    repo_repo: RepoRepository = Depends(get_repo_repository),
    node_client: HubNodeClient = Depends(get_node_client),
    write_target_repo: WriteTargetRepository = Depends(get_write_target_repository),
    write_target_policy: WriteTargetPolicy = Depends(get_write_target_policy),
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),
    llm_client: LLMServiceClient = Depends(get_llm_service_client),
) -> PolicyAwareToolRouter:
    return PolicyAwareToolRouter(
        registry=registry,
        policy_engine=policy_engine,
        node_repo=node_repo,
        repo_repo=repo_repo,
        node_client=node_client,
        write_target_repo=write_target_repo,
        write_target_policy=write_target_policy,
        llm_service_policy=llm_service_policy,
        llm_client=llm_client,
    )
```

### Step 8: Add Timeout Config

**File**: `src/hub/config.py`

Add LLM client timeout configuration:

```python
class HubConfig(BaseSettings):
    # ... existing fields ...
    
    # LLM client settings
    llm_client_timeout: float = Field(120.0, description="Default timeout for LLM service calls")
```

## Validation Plan

### Unit Tests

| Test | Description |
|------|-------------|
| `test_chat_llm_validates_service` | Verify service_id is validated before call |
| `test_chat_llm_rejects_unknown_service` | Verify unknown service returns error |
| `test_chat_llm_returns_latency_metadata` | Verify response includes latency_ms |
| `test_chat_llm_handles_service_error` | Verify service errors are properly handled |
| `test_llm_client_builds_correct_payload` | Verify payload format for different service types |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_chat_llm_round_trip` | Full round-trip with mock LLM service |
| `test_llm_policy_enforces_registration` | Verify only registered services are accessible |

### Code Quality

- Run `ruff check src/hub/tools/llm.py src/hub/services/llm_client.py`
- Run `ruff format src/hub/tools/llm.py src/hub/services/llm_client.py`
- Verify all type hints are complete

## Integration Points

| Component | Integration | Status |
|-----------|-------------|--------|
| LLMServicePolicy | Service validation via `validate_service_access()` | Existing (CORE-002) |
| PolicyEngine | Unified policy with `validate_llm_service()` | Existing (CORE-005) |
| MCP Tool Framework | Tool registration via ToolRegistry | Existing (CORE-006) |
| HTTP Client | httpx.AsyncClient from lifespan | Existing (CORE-004) |

## Risks and Assumptions

1. **Assumption**: LLM services are accessible via HTTP endpoints
2. **Assumption**: Service endpoint configuration includes full URL
3. **Risk**: Different LLM APIs have different response formats - need adapter pattern
4. **Risk**: No session persistence implemented yet (session_id is passed but not used for continuity)

## Blockers / Required User Decisions

None - all necessary components exist or are created by this plan.

## Summary

This plan implements the core `chat_llm` routing functionality:

1. **Service validation** - Uses existing LLMServicePolicy to validate service_id/service_name against registry
2. **Explicit routing** - Direct HTTP client for services with endpoints; extensible to node-agent routing
3. **Structured metadata** - Response includes latency_ms, tokens_used, model, finish_reason

The implementation follows existing patterns (discovery.py, inspection.py) and integrates with the policy-aware routing framework from CORE-006.
