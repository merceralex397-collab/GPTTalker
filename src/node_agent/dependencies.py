"""Dependency injection providers for the node agent."""

from fastapi import Depends, HTTPException, Request

from src.node_agent.config import NodeAgentConfig
from src.node_agent.executor import OperationExecutor


def get_config(request: Request) -> NodeAgentConfig:
    """Get node agent configuration from app state."""
    app = request.app
    if not hasattr(app.state, "config") or app.state.config is None:
        raise RuntimeError("Node agent config not initialized")
    return app.state.config


def get_executor(request: Request) -> OperationExecutor:
    """Get operation executor from app state."""
    app = request.app
    if not hasattr(app.state, "executor") or app.state.executor is None:
        raise RuntimeError("Operation executor not initialized")
    return app.state.executor


async def require_api_key(
    request: Request,
    config: NodeAgentConfig = Depends(get_config),
) -> None:
    """Validate API key authentication if configured.

    Raises HTTPException 401 if auth is configured but request has no valid bearer token.
    """
    if config.api_key is None:
        # Auth not configured - allow all requests (node is open)
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]  # Strip "Bearer " prefix
    if token != config.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
