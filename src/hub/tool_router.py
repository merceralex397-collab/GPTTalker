"""Tool routing primitives for MCP tool handlers."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.hub.tool_routing.requirements import PolicyRequirement

logger = get_logger(__name__)


# Type alias for tool handler functions
ToolHandler = Callable[..., Coroutine[Any, Any, dict[str, Any]]]


@dataclass
class ToolDefinition:
    """Definition of an MCP tool.

    Attributes:
        name: Tool name.
        description: Tool description.
        handler: Async handler function.
        parameters: JSON schema for tool parameters.
        policy: Policy requirements for access control (CORE-006).
        requires_policy_check: Legacy field for backward compatibility.
    """

    name: str
    description: str
    handler: ToolHandler
    parameters: dict[str, Any] = field(default_factory=dict)
    policy: PolicyRequirement | None = None  # Policy requirements (CORE-006)
    requires_policy_check: bool = True  # Default: require policy validation


class ToolRegistry:
    """Registry for MCP tool handlers.

    Maintains a mapping of tool names to their handlers and definitions.
    This is the baseline structure - CORE-006 will add full routing logic.
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, definition: ToolDefinition) -> None:
        """Register a tool handler.

        Args:
            definition: The tool definition including name, description, and handler.
        """
        self._tools[definition.name] = definition
        self._handlers[definition.name] = definition.handler
        logger.info("tool_registered", tool_name=definition.name)

    def register_handler(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool handler with inline parameters.

        Args:
            name: Tool name.
            description: Tool description.
            handler: Async handler function.
            parameters: Optional JSON schema for tool parameters.
        """
        definition = ToolDefinition(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters or {},
        )
        self.register(definition)

    def get_handler(self, tool_name: str) -> ToolHandler | None:
        """Get a registered tool handler by name.

        Args:
            tool_name: Name of the tool.

        Returns:
            The handler function, or None if not found.
        """
        return self._handlers.get(tool_name)

    def get_definition(self, tool_name: str) -> ToolDefinition | None:
        """Get a tool definition by name.

        Args:
            tool_name: Name of the tool.

        Returns:
            The tool definition, or None if not found.
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools.

        Returns:
            List of tool definitions as dictionaries.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self._tools.values()
        ]

    def is_registered(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of the tool.

        Returns:
            True if the tool is registered, False otherwise.
        """
        return tool_name in self._tools

    def get_policy_requirements(self, tool_name: str) -> PolicyRequirement | None:
        """Get policy requirements for a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            PolicyRequirement if defined, None otherwise.
        """
        definition = self._tools.get(tool_name)
        if definition is None:
            return None
        return definition.policy

    @property
    def tool_count(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)


class ToolRouter:
    """Routes tool calls to appropriate handlers.

    This is the baseline router - CORE-006 will integrate
    policy engine validation before execution.
    """

    def __init__(self, registry: ToolRegistry | None = None):
        """Initialize the tool router.

        Args:
            registry: Optional tool registry. Creates a new one if not provided.
        """
        self._registry = registry or ToolRegistry()

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self._registry

    async def route_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Route a tool call to its handler.

        This baseline implementation directly invokes the handler.
        Future tickets (CORE-005, CORE-006) will add:
        - Policy engine validation before execution
        - Full routing logic with fallbacks

        Args:
            tool_name: Name of the tool to invoke.
            parameters: Parameters for the tool.
            trace_id: Optional trace ID for logging.

        Returns:
            Tool execution result.

        Raises:
            ValueError: If the tool is not registered.
        """
        handler = self._registry.get_handler(tool_name)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Log the tool call
        logger.info(
            "tool_call_routed",
            tool_name=tool_name,
            trace_id=trace_id,
            param_keys=list(parameters.keys()) if parameters else [],
        )

        # Invoke the handler
        try:
            result = await handler(**parameters)
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            logger.error(
                "tool_call_failed",
                tool_name=tool_name,
                error=str(e),
                trace_id=trace_id,
            )
            return {
                "success": False,
                "error": str(e),
            }


# Global registry instance for the hub
_global_registry: ToolRegistry | None = None


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        The global ToolRegistry instance.
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator to register a tool handler.

    Args:
        name: Tool name.
        description: Tool description.
        parameters: Optional JSON schema for parameters.

    Returns:
        Decorator function that registers the handler.
    """

    def decorator(handler: ToolHandler) -> ToolHandler:
        registry = get_global_registry()
        registry.register_handler(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters,
        )
        return handler

    return decorator
