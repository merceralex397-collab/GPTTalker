# CORE-006: MCP Tool Routing Framework - Implementation Plan

## Ticket Summary

**ID**: CORE-006  
**Title**: MCP tool routing framework  
**Wave**: 1  
**Lane**: hub-core  
**Summary**: Create the hub-side tool routing framework that maps exposed MCP tools to validated execution paths and shared response formatting.  
**Depends On**: SETUP-004, CORE-002, CORE-005

---

## Acceptance Criteria

1. **Tool registration boundary is defined** - Tools declare their policy requirements at registration time
2. **Routing integrates policy checks before execution** - Every tool call validates against PolicyEngine before handler invocation
3. **Shared error formatting follows the MCP-safe contract** - All errors use standardized MCP JSON-RPC 2.0 error responses

---

## Technical Context

### Existing Infrastructure

| Component | Source | Purpose |
|-----------|--------|---------|
| `ToolRegistry` | SETUP-004 | Basic tool registration and discovery |
| `ToolRouter` | SETUP-004 | Routes tool calls to handlers (no policy) |
| `ToolDefinition` | SETUP-004 | Tool metadata (name, description, handler) |
| `PolicyEngine` | CORE-005 | Unified validation chains (read/write/LLM) |
| Policy classes | CORE-002 | NodePolicy, RepoPolicy, WriteTargetPolicy, LLMServicePolicy |
| DI providers | CORE-002 | `get_policy_engine` dependency |
| MCP transport | SETUP-004 | `format_tool_response`, `format_tool_list` |
| Exceptions | SETUP-002 | GPTTalkerError hierarchy with trace_id support |

### Gap Analysis

The current `ToolRouter.route_tool()` directly invokes handlers without any policy validation:

```python
# Current (from tool_router.py line 182-188)
result = await handler(**parameters)
return {"success": True, "result": result}
```

This bypasses all security checks. CORE-006 must add policy integration at the routing layer.

---

## Design

### 1. Tool Registration Boundary

Tools declare their policy requirements at registration time. This allows the router to know what validations are needed before invoking each handler.

**New `PolicyRequirement` dataclass:**

```python
from dataclasses import dataclass
from src.hub.policy.scopes import OperationScope

@dataclass
class PolicyRequirement:
    """Declares what policy checks a tool requires."""
    scope: OperationScope  # READ, WRITE, or EXECUTE
    requires_node: bool = True       # Must validate node access
    requires_repo: bool = False      # Must validate repo access (if repo_id param)
    requires_write_target: bool = False  # Must validate write target (for writes)
    requires_llm_service: bool = False    # Must validate LLM service (for LLM calls)
    node_param: str = "node_id"       # Parameter name for node ID
    repo_param: str = "repo_id"      # Parameter name for repo ID
    path_param: str = "path"         # Parameter name for file path
    extension_param: str = "extension"  # Parameter name for file extension
    service_param: str = "service_id" # Parameter name for LLM service ID
```

**Updated `ToolDefinition`:**

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: ToolHandler
    parameters: dict[str, Any] = field(default_factory=dict)
    policy: PolicyRequirement | None = None  # NEW: Policy requirements
    requires_policy_check: bool = True  # Keep for backward compat
```

### 2. Policy-Aware Tool Router

Create a new `PolicyAwareToolRouter` that integrates with `PolicyEngine`:

```python
class PolicyAwareToolRouter:
    """Tool router with integrated policy validation.
    
    Validates all tool calls against PolicyEngine before execution.
    Implements fail-closed behavior: if policy check fails, handler is not invoked.
    """
    
    def __init__(
        self, 
        registry: ToolRegistry,
        policy_engine: PolicyEngine,
    ):
        self._registry = registry
        self._policy_engine = policy_engine
    
    async def route_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Route tool call with policy validation."""
        
        # 1. Check tool is registered
        definition = self._registry.get_definition(tool_name)
        if not definition:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        # 2. Extract policy requirements
        policy_req = definition.policy
        if policy_req is None:
            # No policy required - direct execution
            return await self._execute_handler(definition.handler, parameters, trace_id)
        
        # 3. Build validation context
        context = ValidationContext(
            scope=policy_req.scope,
            trace_id=trace_id,
            caller=tool_name,
        )
        
        # 4. Run policy validation based on requirements
        validation_error = await self._validate_policy(policy_req, parameters, context)
        if validation_error:
            return {"success": False, "error": validation_error}
        
        # 5. Execute handler
        return await self._execute_handler(definition.handler, parameters, trace_id)
```

### 3. Error Formatting (MCP-Safe Contract)

All errors use MCP JSON-RPC 2.0 format via the existing `format_tool_response` but with standardized error codes:

```python
# MCP error codes (JSON-RPC 2.0 + MCP-specific)
MCP_ERROR_CODES = {
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603,
    # MCP-specific codes
    "POLICY_VIOLATION": -32000,
    "UNKNOWN_TOOL": -32001,
    "VALIDATION_FAILED": -32002,
    "ACCESS_DENIED": -32003,
}

def format_mcp_error(
    message: str,
    code: int = MCP_ERROR_CODES["INTERNAL_ERROR"],
    trace_id: str | None = None,
    details: dict | None = None,
) -> dict[str, Any]:
    """Format error for MCP response with standardized codes."""
    return {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message,
            "data": details,  # Additional error context
        },
        "trace_id": trace_id,
    }
```

### 4. Tool Handler Interface

Standardize the handler signature with typed parameters:

```python
from typing import TypedDict

class ToolContext(TypedDict):
    """Context passed to all tool handlers."""
    trace_id: str | None
    policy_result: ValidationResult | None  # Pre-validated policy result

class ToolResult(TypedDict):
    """Standard tool result structure."""
    success: bool
    data: Any | None
    error: str | None
    trace_id: str | None

# Handler signature
async def example_handler(
    params: dict[str, Any],
    context: ToolContext,
) -> ToolResult:
    ...
```

---

## Implementation Steps

### Step 1: Create Policy-Aware Router Module

**File**: `src/hub/tool_routing/policy_router.py` (new)

Create the `PolicyAwareToolRouter` class with:

- Integration with `PolicyEngine`
- Policy requirement extraction from parameters
- Validation chain for read/write/LLM operations
- Error handling with MCP-safe formatting

### Step 2: Define Policy Requirements

**File**: `src/hub/tool_routing/requirements.py` (new)

Create:

- `PolicyRequirement` dataclass
- `ToolContext` and `ToolResult` TypedDicts
- Helper functions to extract params for policy checks
- Decorator factory for easy policy requirement declaration

### Step 3: Create Error Formatting Utilities

**File**: `src/hub/tool_routing/errors.py` (new)

Create:

- MCP error code constants
- `format_mcp_error()` function
- `ToolExecutionError` exception class
- Error message templates

### Step 4: Update Tool Registry

**Modify**: `src/hub/tool_router.py`

- Add `policy` field to `ToolDefinition`
- Add `get_policy_requirements()` method
- Keep backward compatibility with existing tools

### Step 5: Add DI Provider for Policy-Aware Router

**Modify**: `src/hub/dependencies.py`

Add:

```python
async def get_policy_aware_router(
    registry: ToolRegistry = Depends(get_tool_registry),  # NEW
    policy_engine: PolicyEngine = Depends(get_policy_engine),
) -> PolicyAwareToolRouter:
    """Get the policy-aware tool router."""
    return PolicyAwareToolRouter(registry=registry, policy_engine=policy_engine)
```

### Step 6: Update MCP Protocol Handler

**Modify**: `src/hub/mcp.py`

- Update `MCPProtocolHandler` to use `PolicyAwareToolRouter`
- Update error handling to use MCP-safe format

### Step 7: Create Tool Registration Module

**File**: `src/hub/tool_routing/__init__.py` (new)

Export:

- `PolicyAwareToolRouter`
- `PolicyRequirement`
- `ToolContext`, `ToolResult`
- `format_mcp_error`
- Registration helpers

### Step 8: Export Updates

**Modify**: `src/hub/__init__.py`

- Export new routing components
- Update imports

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `src/hub/tool_routing/__init__.py` | Package exports |
| `src/hub/tool_routing/policy_router.py` | PolicyAwareToolRouter |
| `src/hub/tool_routing/requirements.py` | PolicyRequirement, tool types |
| `src/hub/tool_routing/errors.py` | MCP error formatting |

### Modified Files

| File | Changes |
|------|---------|
| `src/hub/tool_router.py` | Add policy field to ToolDefinition |
| `src/hub/dependencies.py` | Add DI provider for PolicyAwareToolRouter |
| `src/hub/mcp.py` | Use PolicyAwareToolRouter |
| `src/hub/__init__.py` | Export new components |

---

## Validation Plan

### Unit Tests

1. **PolicyAwareToolRouter tests**:
   - `test_unknown_tool_returns_error` - Unknown tool returns error
   - `test_read_operation_validates_node` - Read ops validate node
   - `test_write_operation_validates_write_target` - Write ops validate target
   - `test_policy_violation_returns_error` - Failed policy returns error
   - `test_handler_executed_after_policy_pass` - Handler runs only after validation

2. **PolicyRequirement tests**:
   - `test_extract_node_id_from_params` - Correct param extraction
   - `test_default_requirements` - Default values work correctly

3. **Error formatting tests**:
   - `test_mcp_error_format` - Error format matches MCP spec
   - `test_error_codes` - Correct error codes used

### Integration Tests

4. **Router + PolicyEngine integration**:
   - Full validation chain from tool call to handler execution
   - Verify policy engine methods are called with correct params

5. **MCP protocol integration**:
   - End-to-end tool call through MCPProtocolHandler
   - Verify error responses are MCP-compliant

### Validation Commands

```bash
# Run tests
python -m pytest tests/hub/tool_routing/ -v

# Run linting
python -m ruff check src/hub/tool_routing/

# Type checking
python -m mypy src/hub/tool_routing/
```

---

## Integration Points

| Component | Integration | Method |
|-----------|-------------|--------|
| PolicyEngine | Policy validation | DI provider |
| ToolRegistry | Tool discovery | Instance reference |
| MCP transport | Response formatting | `format_tool_response` |
| Exceptions | Error handling | GPTTalkerError hierarchy |
| Tracing | Request tracking | trace_id propagation |

---

## Risks and Assumptions

### Risks

1. **Performance impact**: Policy validation adds latency to each tool call
   - Mitigation: Cache policy results where possible, async validation

2. **Breaking existing tools**: Adding policy requirements may break tools registered before CORE-006
   - Mitigation: Default to `requires_policy_check: False` for backward compatibility

3. **Parameter extraction complexity**: Some tools may use non-standard parameter names
   - Mitigation: Allow custom param name configuration in PolicyRequirement

### Assumptions

1. **PolicyEngine is available**: Assumes CORE-005 PolicyEngine is instantiated and available via DI
2. **Tool handlers are async**: All tool handlers follow async Callable signature
3. **Parameter extraction**: Tool parameters are flat dicts (not nested objects)

---

## Blockers and Decisions

### None Required

All blocking decisions have been resolved:
- PolicyEngine integration approach is clear from CORE-005
- MCP error format follows JSON-RPC 2.0 (already in SETUP-004)
- DI pattern is consistent with existing codebase

---

## Summary

CORE-006 creates a policy-integrated tool routing framework that:

1. **Defines tool registration boundary** - Tools declare policy requirements at registration
2. **Integrates policy checks before execution** - PolicyEngine validates all tool calls
3. **Uses MCP-safe error formatting** - Standardized JSON-RPC 2.0 error responses

The implementation adds a thin policy validation layer around the existing tool routing, reusing all PolicyEngine functionality from CORE-005 while maintaining backward compatibility with existing tools.
