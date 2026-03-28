"""Tests for tool routing framework."""

import pytest

from src.hub.policy.scopes import OperationScope
from src.hub.tool_router import (
    ToolDefinition,
    ToolRegistry,
    ToolRouter,
    get_global_registry,
    register_tool,
)
from src.hub.tool_routing.requirements import (
    READ_REPO_REQUIREMENT,
)


# Sample async handler for testing
async def mock_handler(**kwargs):
    """Mock tool handler for testing."""
    return {"result": "success", "params": kwargs}


async def another_handler(name: str = "default"):
    """Another mock handler with parameters."""
    return {"greeting": f"hello {name}"}


# =============================================================================
# Happy-path tests
# =============================================================================


def test_tool_registry_register():
    """Test registering a tool directly via ToolDefinition."""
    registry = ToolRegistry()
    definition = ToolDefinition(
        name="test_tool",
        description="A test tool",
        handler=mock_handler,
    )
    registry.register(definition)
    assert registry.is_registered("test_tool")
    assert registry.tool_count == 1


def test_tool_registry_register_handler():
    """Test registering a tool using register_handler method."""
    registry = ToolRegistry()
    registry.register_handler(
        name="test_tool",
        description="A test tool",
        handler=mock_handler,
    )
    assert registry.is_registered("test_tool")


def test_tool_registry_get_handler():
    """Test retrieving a registered handler by name."""
    registry = ToolRegistry()
    registry.register_handler(
        name="test_tool",
        description="A test tool",
        handler=mock_handler,
    )
    handler = registry.get_handler("test_tool")
    assert handler is not None
    assert callable(handler)


def test_tool_registry_get_definition():
    """Test retrieving a tool definition with all fields."""
    registry = ToolRegistry()
    definition = ToolDefinition(
        name="test_tool",
        description="A test tool",
        handler=mock_handler,
        parameters={"type": "object"},
        policy=READ_REPO_REQUIREMENT,
    )
    registry.register(definition)

    retrieved = registry.get_definition("test_tool")
    assert retrieved is not None
    assert retrieved.name == "test_tool"
    assert retrieved.description == "A test tool"
    assert retrieved.parameters == {"type": "object"}
    assert retrieved.policy == READ_REPO_REQUIREMENT


def test_tool_registry_list_tools():
    """Test listing all registered tools."""
    registry = ToolRegistry()
    registry.register_handler(
        name="tool_one",
        description="First tool",
        handler=mock_handler,
    )
    registry.register_handler(
        name="tool_two",
        description="Second tool",
        handler=another_handler,
    )

    tools = registry.list_tools()
    assert len(tools) == 2
    tool_names = [t["name"] for t in tools]
    assert "tool_one" in tool_names
    assert "tool_two" in tool_names


def test_tool_registry_is_registered():
    """Test checking if a tool is registered."""
    registry = ToolRegistry()
    registry.register_handler(
        name="test_tool",
        description="A test tool",
        handler=mock_handler,
    )

    assert registry.is_registered("test_tool") is True
    assert registry.is_registered("nonexistent") is False


def test_tool_registry_tool_count():
    """Test counting registered tools."""
    registry = ToolRegistry()
    assert registry.tool_count == 0

    registry.register_handler(
        name="tool_one",
        description="First tool",
        handler=mock_handler,
    )
    assert registry.tool_count == 1

    registry.register_handler(
        name="tool_two",
        description="Second tool",
        handler=another_handler,
    )
    assert registry.tool_count == 2


@pytest.mark.asyncio
async def test_tool_router_route_tool_success():
    """Test routing a tool call to its handler successfully."""
    registry = ToolRegistry()
    registry.register_handler(
        name="greet",
        description="Greet someone",
        handler=another_handler,
    )

    router = ToolRouter(registry)
    result = await router.route_tool("greet", {"name": "World"})

    assert result["success"] is True
    assert result["result"]["greeting"] == "hello World"


@pytest.mark.asyncio
async def test_tool_router_get_policy_requirements():
    """Test retrieving policy requirements for a registered tool."""
    registry = ToolRegistry()
    definition = ToolDefinition(
        name="read_repo",
        description="Read repository",
        handler=mock_handler,
        policy=READ_REPO_REQUIREMENT,
    )
    registry.register(definition)

    policy = registry.get_policy_requirements("read_repo")
    assert policy is not None
    assert policy.scope == OperationScope.READ
    assert policy.requires_repo is True


def test_get_global_registry_singleton():
    """Test that get_global_registry returns a singleton."""
    reg1 = get_global_registry()
    reg2 = get_global_registry()
    assert reg1 is reg2


def test_register_tool_decorator():
    """Test using the @register_tool decorator."""
    # Note: This test uses a fresh registry to avoid pollution
    global _test_registry
    from src.hub.tool_router import _global_registry

    original = _global_registry
    from src.hub import tool_router

    tool_router._global_registry = ToolRegistry()

    @register_tool(
        name="decorator_tool",
        description="A decorated tool",
        parameters={"type": "object"},
    )
    async def decorated_handler(**kwargs):
        return {"decorated": True}

    assert tool_router._global_registry.is_registered("decorator_tool")
    tool_router._global_registry = original


# =============================================================================
# Error-path tests
# =============================================================================


@pytest.mark.asyncio
async def test_tool_router_route_unknown_tool():
    """Test that routing an unknown tool raises ValueError."""
    registry = ToolRegistry()
    router = ToolRouter(registry)

    with pytest.raises(ValueError, match="Unknown tool"):
        await router.route_tool("nonexistent_tool", {})


def test_tool_registry_get_handler_not_found():
    """Test that getting a non-existent handler returns None."""
    registry = ToolRegistry()
    handler = registry.get_handler("nonexistent")
    assert handler is None


def test_get_handler_returns_none_for_unknown():
    """Test that get_handler returns None for unknown tools."""
    registry = ToolRegistry()
    result = registry.get_handler("unknown_tool_xyz")
    assert result is None
