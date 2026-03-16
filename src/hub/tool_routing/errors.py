"""MCP error formatting utilities.

This module provides MCP-compliant error formatting using JSON-RPC 2.0
error codes and standardized error messages.
"""

from enum import IntEnum
from typing import Any


class MCPErrorCode(IntEnum):
    """MCP-specific error codes based on JSON-RPC 2.0.

    Standard JSON-RPC 2.0 error codes:
    -32700: Parse error
    -32600: Invalid Request
    -32601: Method not found
    -32602: Invalid params
    -32603: Internal error

    MCP-specific error codes:
    -32000: Policy violation
    -32001: Unknown tool
    -32002: Validation failed
    -32003: Access denied
    """

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific codes
    POLICY_VIOLATION = -32000
    UNKNOWN_TOOL = -32001
    VALIDATION_FAILED = -32002
    ACCESS_DENIED = -32003


# Error code mapping for human-readable messages
ERROR_CODE_MESSAGES = {
    MCPErrorCode.PARSE_ERROR: "Parse error - Invalid JSON",
    MCPErrorCode.INVALID_REQUEST: "Invalid request - Missing or invalid parameters",
    MCPErrorCode.METHOD_NOT_FOUND: "Method not found",
    MCPErrorCode.INVALID_PARAMS: "Invalid parameters",
    MCPErrorCode.INTERNAL_ERROR: "Internal error",
    MCPErrorCode.POLICY_VIOLATION: "Policy violation - Operation not allowed",
    MCPErrorCode.UNKNOWN_TOOL: "Unknown tool - Tool not registered",
    MCPErrorCode.VALIDATION_FAILED: "Validation failed - Input validation error",
    MCPErrorCode.ACCESS_DENIED: "Access denied - Insufficient permissions",
}


def format_mcp_error(
    message: str,
    code: int = MCPErrorCode.INTERNAL_ERROR,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format error for MCP response with standardized codes.

    Creates a properly formatted MCP JSON-RPC 2.0 error response.

    Args:
        message: Human-readable error message.
        code: JSON-RPC error code (defaults to INTERNAL_ERROR).
        trace_id: Optional trace ID for request correlation.
        details: Additional error context or data.

    Returns:
        MCP-formatted error response dictionary.
    """
    error_response: dict[str, Any] = {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message,
        },
    }

    if details:
        error_response["error"]["data"] = details

    if trace_id:
        error_response["trace_id"] = trace_id

    return error_response


def format_policy_error(
    reason: str,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format a policy violation error.

    Args:
        reason: Human-readable reason for policy rejection.
        trace_id: Optional trace ID for request correlation.
        details: Additional context about the policy failure.

    Returns:
        MCP-formatted policy error response.
    """
    return format_mcp_error(
        message=f"Policy violation: {reason}",
        code=MCPErrorCode.POLICY_VIOLATION,
        trace_id=trace_id,
        details=details,
    )


def format_unknown_tool_error(
    tool_name: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Format an unknown tool error.

    Args:
        tool_name: Name of the unknown tool.
        trace_id: Optional trace ID for request correlation.

    Returns:
        MCP-formatted unknown tool error response.
    """
    return format_mcp_error(
        message=f"Unknown tool: {tool_name}",
        code=MCPErrorCode.UNKNOWN_TOOL,
        trace_id=trace_id,
        details={"tool_name": tool_name},
    )


def format_validation_error(
    message: str,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format a validation error.

    Args:
        message: Human-readable validation error message.
        trace_id: Optional trace ID for request correlation.
        details: Additional validation error context.

    Returns:
        MCP-formatted validation error response.
    """
    return format_mcp_error(
        message=f"Validation failed: {message}",
        code=MCPErrorCode.VALIDATION_FAILED,
        trace_id=trace_id,
        details=details,
    )


def format_access_denied_error(
    resource: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Format an access denied error.

    Args:
        resource: Resource that access was denied to.
        trace_id: Optional trace ID for request correlation.

    Returns:
        MCP-formatted access denied error response.
    """
    return format_mcp_error(
        message=f"Access denied to resource: {resource}",
        code=MCPErrorCode.ACCESS_DENIED,
        trace_id=trace_id,
        details={"resource": resource},
    )


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails.

    This exception is used internally to signal tool execution failures
    and is converted to MCP error format by the routing layer.
    """

    def __init__(
        self,
        message: str,
        code: int = MCPErrorCode.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
    ):
        """Initialize tool execution error.

        Args:
            message: Human-readable error message.
            code: MCP error code (defaults to INTERNAL_ERROR).
            details: Additional error context.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_mcp_error(self, trace_id: str | None = None) -> dict[str, Any]:
        """Convert to MCP error format.

        Args:
            trace_id: Optional trace ID for correlation.

        Returns:
            MCP-formatted error response.
        """
        return format_mcp_error(
            message=self.message,
            code=self.code,
            trace_id=trace_id,
            details=self.details,
        )


class PolicyViolationError(ToolExecutionError):
    """Exception raised when a policy check fails."""

    def __init__(
        self,
        reason: str,
        details: dict[str, Any] | None = None,
    ):
        """Initialize policy violation error.

        Args:
            reason: Human-readable reason for policy rejection.
            details: Additional context about the policy failure.
        """
        super().__init__(
            message=f"Policy violation: {reason}",
            code=MCPErrorCode.POLICY_VIOLATION,
            details=details,
        )
        self.reason = reason


class ValidationError(ToolExecutionError):
    """Exception raised when input validation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        """Initialize validation error.

        Args:
            message: Human-readable validation error message.
            details: Additional validation context.
        """
        super().__init__(
            message=f"Validation failed: {message}",
            code=MCPErrorCode.VALIDATION_FAILED,
            details=details,
        )
