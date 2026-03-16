# CORE-006: MCP Tool Routing Framework - Implementation Summary

## Ticket Summary

- **ID**: CORE-006
- **Title**: MCP tool routing framework
- **Wave**: 1
- **Lane**: hub-core
- **Summary**: Create the hub-side tool routing framework that maps exposed MCP tools to validated execution paths and shared response formatting.
- **Depends On**: SETUP-004, CORE-002, CORE-005

---

## Acceptance Criteria Status

| Criterion | Status | Notes |
|-----------|--------|-------|
| Tool registration boundary is defined | ✅ Complete | PolicyRequirement dataclass added to ToolDefinition |
| Routing integrates policy checks before execution | ✅ Complete | PolicyAwareToolRouter validates all tool calls - default is fail-closed |
| Shared error formatting follows MCP-safe contract | ✅ Complete | MCP error codes and format_mcp_error() implemented |

---

## Implementation Details

### New Files Created

#### 1. `src/hub/tool_routing/__init__.py` - Package Exports
- Exports all tool routing components
- Includes PolicyAwareToolRouter, PolicyRequirement, error formatters
- Provides pre-defined requirements (READ_REPO_REQUIREMENT, WRITE_REQUIREMENT, etc.)
- Helper functions: create_read_requirement(), create_write_requirement(), create_llm_requirement()

#### 2. `src/hub/tool_routing/policy_router.py` - PolicyAwareToolRouter
- Integrates PolicyEngine validation with tool execution
- Implements fail-closed behavior: policy checks must pass before handler invocation
- Validates node_id, repo_id, path, extension, service_id based on policy requirements
- Returns structured MCP-formatted errors on validation failure
- Sanitizes parameters for logging (redacts sensitive keys)

#### 3. `src/hub/tool_routing/requirements.py` - Policy Requirements
- `PolicyRequirement` dataclass: declares what policy checks a tool requires
- `ToolContext` and `ToolResult` TypedDicts for handler interfaces
- Helper methods to extract parameters (node_id, repo_id, path, etc.)
- Pre-defined requirements: READ_REPO_REQUIREMENT, WRITE_REQUIREMENT, LLM_REQUIREMENT, NO_POLICY_REQUIREMENT
- Factory functions: create_read_requirement(), create_write_requirement(), create_llm_requirement()

#### 4. `src/hub/tool_routing/errors.py` - MCP Error Formatting
- `MCPErrorCode` IntEnum with JSON-RPC 2.0 codes (-32700 to -32003)
- `format_mcp_error()` - main error formatting function
- Specialized formatters: format_policy_error(), format_unknown_tool_error(), format_validation_error(), format_access_denied_error()
- Exception classes: ToolExecutionError, ValidationError, PolicyViolationError

### Modified Files

#### 1. `src/hub/tool_router.py`
- Added `policy: PolicyRequirement | None` field to ToolDefinition
- Added `get_policy_requirements()` method to ToolRegistry
- Uses TYPE_CHECKING to avoid circular imports

#### 2. `src/hub/dependencies.py`
- Added imports for PolicyAwareToolRouter, ToolRegistry
- Added `get_tool_registry()` DI provider
- Added `get_policy_aware_router()` DI provider for PolicyAwareToolRouter

#### 3. `src/hub/mcp.py`
- Updated to use PolicyAwareToolRouter
- Added lazy router initialization fallback
- Updated error handling to use MCP-safe format

#### 4. `src/hub/__init__.py`
- Exports PolicyAwareToolRouter, PolicyRequirement, error formatting functions
- Lazy-loads app to avoid circular imports

---

## Integration Points

| Component | Integration Method |
|-----------|-------------------|
| PolicyEngine | Injected via DI in PolicyAwareToolRouter |
| ToolRegistry | Via ToolDefinition.policy field |
| MCP transport | Uses format_tool_response() for results |
| Error handling | MCPErrorCode enum + format_mcp_error() |
| Tracing | trace_id propagation throughout |

---

## Usage Example

```python
from src.hub.tool_routing import (
    PolicyAwareToolRouter,
    PolicyRequirement,
    create_read_requirement,
    create_write_requirement,
)
from src.hub.tool_router import ToolDefinition

# Define policy requirements for a tool
read_repo_policy = create_read_requirement(requires_repo=True)

# Register tool with policy
definition = ToolDefinition(
    name="read_file",
    description="Read a file from a repo",
    handler=read_file_handler,
    policy=create_read_requirement(requires_repo=True, repo_param="repo_id"),
)

# Use PolicyAwareToolRouter (via DI in FastAPI)
result = await router.route_tool(
    tool_name="read_file",
    parameters={"repo_id": "my-repo", "path": "/path/to/file.md"},
    trace_id="abc-123",
)
```

---

## Validation

- All linting passes (ruff check)
- Imports tested successfully
- Circular import issues resolved with TYPE_CHECKING pattern

---

## Code Review Fix (Applied)

### Issue: Default policy behavior was inverted (Medium Severity)

**Problem**: When no policy was explicitly set, `_get_policy_requirement()` returned `None` which caused validation to be **skipped** rather than enforced. This contradicted the fail-closed principle.

**Fix Applied**:
- Changed the default behavior in `policy_router.py` from returning `None` to returning `READ_NODE_REQUIREMENT`
- Now unknown tools without explicit policy go through basic node validation
- This ensures fail-closed behavior: unknown tools are not allowed through without checks
- Only tools that explicitly opt-out via `requires_policy_check=False` can skip validation

**Code Change** (in `_get_policy_requirement` method):
```python
# Before (incorrect - skip validation):
return None  # Will be handled as no-policy for now

# After (correct - enforce basic validation):
from src.hub.tool_routing.requirements import READ_NODE_REQUIREMENT
return READ_NODE_REQUIREMENT
```

---

## Notes

- Policy validation is fail-closed: unknown nodes, repos, write targets, and services are rejected
- **Default behavior is fail-closed**: tools without explicit policy go through basic node validation via `READ_NODE_REQUIREMENT`
- Only explicit opt-out via `requires_policy_check=False` or `NO_POLICY_REQUIREMENT` skips validation
- The router integrates with the existing PolicyEngine from CORE-005
- Backward compatibility maintained via `requires_policy_check` field
- All error responses follow MCP JSON-RPC 2.0 format
