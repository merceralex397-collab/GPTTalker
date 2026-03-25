"""Dependency injection providers for the node agent."""

from fastapi import Request

from src.node_agent.config import NodeAgentConfig
from src.node_agent.executor import OperationExecutor


def get_config(request: Request) -> NodeAgentConfig:
    """Get node agent configuration from app state.

    Args:
        request: The FastAPI request object.

    Returns:
        NodeAgentConfig instance stored in app state.

    Raises:
        RuntimeError: If config is not initialized in app state.
    """
    app = request.app
    if not hasattr(app.state, "config") or app.state.config is None:
        raise RuntimeError("Node agent config not initialized")
    return app.state.config


def get_executor(request: Request) -> OperationExecutor:
    """Get operation executor from app state.

    Args:
        request: The FastAPI request object.

    Returns:
        OperationExecutor instance stored in app state.

    Raises:
        RuntimeError: If executor is not initialized in app state.
    """
    app = request.app
    if not hasattr(app.state, "executor") or app.state.executor is None:
        raise RuntimeError("Operation executor not initialized")
    return app.state.executor
