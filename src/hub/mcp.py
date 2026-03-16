"""MCP protocol handling for the hub."""

from typing import Any

from src.hub.tool_router import ToolRouter, get_global_registry
from src.hub.transport.mcp import (
    format_tool_list,
    format_tool_response,
    parse_tool_call,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class MCPProtocolHandler:
    """Handles MCP protocol communication between ChatGPT and the hub.

    This is the baseline implementation that routes tool calls to
    registered handlers. Future tickets will add policy validation
    and more sophisticated routing logic.
    """

    def __init__(self):
        """Initialize the MCP protocol handler."""
        self._router = ToolRouter(get_global_registry())

    async def handle_tool_call(
        self,
        tool_name: str,
        parameters: dict,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle an MCP tool call from ChatGPT.

        Args:
            tool_name: Name of the tool to invoke
            parameters: Parameters for the tool
            trace_id: Optional trace ID for request correlation

        Returns:
            Tool response in MCP format
        """
        import time

        start_time = int(time.time() * 1000)

        # Check if tool is registered
        if not self._router.registry.is_registered(tool_name):
            logger.warning(
                "unknown_tool_requested",
                tool_name=tool_name,
                trace_id=trace_id,
            )
            return format_tool_response(
                result=None,
                trace_id=trace_id,
                duration_ms=int(time.time() * 1000) - start_time,
                error=f"Unknown tool: {tool_name}",
            )

        # Route to handler
        result = await self._router.route_tool(
            tool_name=tool_name,
            parameters=parameters,
            trace_id=trace_id,
        )

        duration_ms = int(time.time() * 1000) - start_time

        if result.get("success"):
            return format_tool_response(
                result=result.get("result"),
                trace_id=trace_id,
                duration_ms=duration_ms,
            )
        else:
            return format_tool_response(
                result=None,
                trace_id=trace_id,
                duration_ms=duration_ms,
                error=result.get("error", "Tool execution failed"),
            )

    async def list_tools(self) -> dict[str, Any]:
        """List all available MCP tools.

        Returns:
            MCP-formatted tool list response.
        """
        tools = self._router.registry.list_tools()
        return format_tool_list(tools)

    async def handle_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Handle a raw MCP request.

        Parses the request, routes to the appropriate handler,
        and formats the response.

        Args:
            request_data: Raw MCP request data (JSON-RPC 2.0 format).

        Returns:
            MCP-formatted response.
        """
        method = request_data.get("method")
        message_id = request_data.get("id")
        trace_id = request_data.get("trace_id")

        if method == "tools/call":
            # Parse tool call
            parsed = parse_tool_call(request_data)
            return await self.handle_tool_call(
                tool_name=parsed["tool_name"],
                parameters=parsed["parameters"],
                trace_id=parsed["trace_id"] or trace_id,
            )
        elif method == "tools/list":
            return await self.list_tools()
        else:
            # Unknown method
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }
