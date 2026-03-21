"""Hub handler instances.

This module holds shared handler instances to avoid circular imports
between main.py and routes.py.
"""

from src.hub.mcp import MCPProtocolHandler

# Initialize MCP handler (shared across the hub)
mcp_handler = MCPProtocolHandler()
