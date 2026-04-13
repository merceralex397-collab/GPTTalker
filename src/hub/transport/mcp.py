"""MCP protocol transport implementation."""

from typing import Any

from .base import TransportError, TransportProtocol, TransportResult, TransportStatus


class MCPTransport(TransportProtocol):
    """MCP protocol transport implementation.

    Handles MCP protocol framing and message handling for
    communication between ChatGPT and the hub.
    """

    def __init__(self):
        """Initialize the MCP transport."""
        self._initialized = True

    async def send(self, message: dict[str, Any]) -> TransportResult:
        """Send an MCP message.

        For HTTP-based transport, this is typically a no-op since
        responses are returned directly.

        Args:
            message: The MCP message to send.

        Returns:
            TransportResult with success status.
        """
        try:
            return TransportResult(
                status=TransportStatus.SUCCESS,
                data=message,
                duration_ms=0,
            )
        except Exception as e:
            return TransportResult(
                status=TransportStatus.ERROR,
                error=str(e),
            )

    async def receive(self) -> dict[str, Any] | None:
        """Receive an MCP message.

        For HTTP-based transport, messages are received via
        request bodies rather than this method.

        Returns:
            None for HTTP transport - messages come via request body.
        """
        return None

    async def close(self) -> None:
        """Close the transport connection.

        For HTTP transport, this is a no-op.
        """
        pass


def parse_tool_call(request_data: dict[str, Any]) -> dict[str, Any]:
    """Parse an MCP tool call request.

    Extracts tool name and parameters from an MCP request structure.

    Args:
        request_data: The raw request data from MCP client.

    Returns:
        Dictionary with 'tool_name', 'parameters', 'trace_id', 'message_id'.

    Raises:
        TransportError: If the request format is invalid.
    """
    # Handle MCP JSON-RPC 2.0 format
    method = request_data.get("method")
    if method != "tools/call":
        raise TransportError(f"Unsupported MCP method: {method}")

    params = request_data.get("params", {})
    tool_name = params.get("name")
    if not tool_name:
        raise TransportError("Missing required parameter: name")

    # Extract parameters (MCP passes them as a dict under 'arguments')
    arguments = params.get("arguments", {})

    # Extract trace_id if provided
    trace_id = params.get("trace_id") or request_data.get("trace_id")

    # Extract message ID for correlation
    message_id = request_data.get("id")

    return {
        "tool_name": tool_name,
        "parameters": arguments,
        "trace_id": trace_id,
        "message_id": message_id,
    }


def format_tool_response(
    result: Any,
    trace_id: str | None = None,
    message_id: str | int | None = None,
    duration_ms: int = 0,
    error: str | None = None,
) -> dict[str, Any]:
    """Format a tool result for MCP response.

    Creates a properly formatted MCP JSON-RPC 2.0 response.

    Args:
        result: The tool execution result.
        trace_id: Optional trace ID for correlation.
        message_id: The request ID to correlate response.
        duration_ms: Execution duration in milliseconds.
        error: Optional error message if execution failed.

    Returns:
        Properly formatted MCP JSON-RPC 2.0 response.
    """
    response: dict[str, Any] = {
        "jsonrpc": "2.0",
    }

    if message_id is not None:
        response["id"] = message_id

    if error:
        if isinstance(error, dict):
            error_message = error.get("message", str(error))
        else:
            error_message = error
        response["error"] = {
            "code": -32603,
            "message": error_message,
        }
    else:
        # If handler returned an error dict, promote it to proper JSON-RPC error
        if isinstance(result, dict) and result.get("success") is False and "error" in result:
            response["error"] = {
                "code": -32603,
                "message": result.get("error", "Unknown error"),
            }
            return response

        # If result already has a "data" key, use it directly to avoid double-wrapping
        if isinstance(result, dict) and "data" in result:
            response["result"] = {
                "success": result.get("success", True),
                "data": result["data"],
                "duration_ms": duration_ms,
            }
        else:
            response["result"] = {
                "success": True,
                "data": result,
                "duration_ms": duration_ms,
            }

    if trace_id:
        response["trace_id"] = trace_id

    return response


def format_tool_list(tools: list[dict[str, Any]]) -> dict[str, Any]:
    """Format the list of available tools for MCP.

    Args:
        tools: List of tool definitions with 'name', 'description', 'parameters'.

    Returns:
        MCP-formatted tool list response.
    """
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "inputSchema": tool.get("parameters", {}),
                }
                for tool in tools
            ]
        },
    }
