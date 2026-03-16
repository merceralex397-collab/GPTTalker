"""Tool routing package for MCP tool handling with policy integration.

This package provides:
- PolicyAwareToolRouter: Router with integrated policy validation
- PolicyRequirement: Declarations for tool security requirements
- ToolContext/ToolResult: TypedDicts for handler interfaces
- MCP error formatting utilities
"""

from src.hub.tool_routing.errors import (
    MCPErrorCode,
    PolicyViolationError,
    ToolExecutionError,
    ValidationError,
    format_access_denied_error,
    format_mcp_error,
    format_policy_error,
    format_unknown_tool_error,
    format_validation_error,
)
from src.hub.tool_routing.policy_router import PolicyAwareToolRouter
from src.hub.tool_routing.requirements import (
    LLM_REQUIREMENT,
    NO_POLICY_REQUIREMENT,
    READ_NODE_REQUIREMENT,
    READ_REPO_REQUIREMENT,
    WRITE_REQUIREMENT,
    PolicyRequirement,
    ToolContext,
    ToolResult,
    create_llm_requirement,
    create_read_requirement,
    create_write_requirement,
)

__all__ = [
    # Policy-aware router
    "PolicyAwareToolRouter",
    # Policy requirements
    "PolicyRequirement",
    "READ_REPO_REQUIREMENT",
    "READ_NODE_REQUIREMENT",
    "WRITE_REQUIREMENT",
    "LLM_REQUIREMENT",
    "NO_POLICY_REQUIREMENT",
    "create_read_requirement",
    "create_write_requirement",
    "create_llm_requirement",
    # Tool context and result types
    "ToolContext",
    "ToolResult",
    # Error formatting
    "format_mcp_error",
    "format_policy_error",
    "format_unknown_tool_error",
    "format_validation_error",
    "format_access_denied_error",
    "MCPErrorCode",
    # Exception classes
    "ToolExecutionError",
    "ValidationError",
    "PolicyViolationError",
]
