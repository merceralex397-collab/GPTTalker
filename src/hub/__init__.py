"""Hub package - FastAPI MCP hub server."""

# Export key components for external use
# Note: We avoid importing app here to prevent circular imports
# between main.py and routes.py
from src.hub.tool_routing import (
    PolicyAwareToolRouter,
    PolicyRequirement,
    format_mcp_error,
    format_policy_error,
    format_unknown_tool_error,
)

__all__ = [
    # Tool routing components
    "PolicyAwareToolRouter",
    "PolicyRequirement",
    "format_mcp_error",
    "format_policy_error",
    "format_unknown_tool_error",
]


def get_app():
    """Get the FastAPI application instance.

    This function avoids the circular import issue by lazily loading
    the app only when needed.

    Returns:
        The FastAPI application instance.
    """
    from src.hub.main import app

    return app
