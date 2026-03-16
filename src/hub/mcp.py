"""MCP protocol handling for the hub."""

from typing import Any

from src.hub.tool_router import get_global_registry
from src.hub.tool_routing import PolicyAwareToolRouter
from src.hub.transport.mcp import (
    format_tool_list,
    format_tool_response,
    parse_tool_call,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class MCPProtocolHandler:
    """Handles MCP protocol communication between ChatGPT and the hub.

    This handler routes tool calls to registered handlers with integrated
    policy validation via PolicyAwareToolRouter.
    """

    def __init__(self, router: PolicyAwareToolRouter | None = None):
        """Initialize the MCP protocol handler.

        Args:
            router: Optional PolicyAwareToolRouter. Creates one if not provided.
        """
        self._router = router

    def _ensure_router(self) -> PolicyAwareToolRouter:
        """Ensure router is initialized.

        Returns:
            PolicyAwareToolRouter instance.

        Raises:
            RuntimeError: If router is not set and cannot be created.
        """
        if self._router is None:
            # Lazy initialization using dependency

            # Create a simple synchronous version for basic usage
            registry = get_global_registry()
            # Note: In actual FastAPI usage, the router will be injected via DI
            # This is a fallback for non-FastAPI usage
            import asyncio

            from src.hub.dependencies import get_policy_engine

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't synchronously get policy engine in async context
                    raise RuntimeError(
                        "PolicyAwareToolRouter not initialized. Use FastAPI dependency injection."
                    )
                policy_engine = loop.run_until_complete(get_policy_engine())
                self._router = PolicyAwareToolRouter(
                    registry=registry,
                    policy_engine=policy_engine,
                )
            except RuntimeError as err:
                raise RuntimeError(
                    "PolicyAwareToolRouter not initialized. Use FastAPI dependency injection."
                ) from err
        return self._router

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

        # Ensure router is available
        router = self._ensure_router()

        # Check if tool is registered
        if not router.registry.is_registered(tool_name):
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

        # Route to handler with policy validation
        result = await router.route_tool(
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
        router = self._ensure_router()
        tools = router.registry.list_tools()
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
