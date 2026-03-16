"""Dependency injection providers for the node agent."""

from fastapi import Depends, FastAPI

from src.node_agent.config import NodeAgentConfig
from src.node_agent.executor import OperationExecutor


def get_config(app: FastAPI) -> NodeAgentConfig:
    """Get node agent configuration from app state.

    Args:
        app: The FastAPI application instance.

    Returns:
        NodeAgentConfig instance stored in app state.

    Raises:
        RuntimeError: If config is not initialized in app state.
    """
    if not hasattr(app.state, "config") or app.state.config is None:
        raise RuntimeError("Node agent config not initialized")
    return app.state.config


def get_executor(app: FastAPI) -> OperationExecutor:
    """Get operation executor from app state.

    Args:
        app: The FastAPI application instance.

    Returns:
        OperationExecutor instance stored in app state.

    Raises:
        RuntimeError: If executor is not initialized in app state.
    """
    if not hasattr(app.state, "executor") or app.state.executor is None:
        raise RuntimeError("Operation executor not initialized")
    return app.state.executor


# Type alias for dependency functions that return config
ConfigDep = Depends[NodeAgentConfig]
# Type alias for dependency functions that return executor
ExecutorDep = Depends[OperationExecutor]
