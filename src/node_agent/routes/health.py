"""Health endpoint for node agent."""

import time
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from src.node_agent.config import NodeAgentConfig
from src.node_agent.dependencies import get_config, get_executor
from src.node_agent.executor import OperationExecutor
from src.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response for node agent."""

    status: Literal["healthy", "degraded", "unhealthy"]
    node_name: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    capabilities: list[str]
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    request: Request,
    config: NodeAgentConfig = Depends(get_config),
    executor: OperationExecutor = Depends(get_executor),
) -> HealthResponse:
    """Health check endpoint for the node agent.

    Returns the current health status of the node agent including
    configuration, uptime, and basic system checks.

    Args:
        response: FastAPI response object for setting status code.
        request: FastAPI request to access app state.
        config: Node agent configuration dependency.
        executor: Operation executor dependency.

    Returns:
        HealthResponse with current node status.
    """
    # Calculate uptime
    app = request.app
    startup_time = getattr(app.state, "startup_time", None)
    if startup_time is not None:
        uptime_seconds = time.time() - startup_time
    else:
        uptime_seconds = 0.0

    # Run basic checks
    checks: dict[str, bool] = {
        "config_valid": config is not None,
        "executor_initialized": executor is not None,
        "allowed_paths_configured": len(executor.allowed_paths) > 0,
    }

    # Determine overall status
    if all(checks.values()):
        status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    elif any(checks.values()):
        status = "degraded"
    else:
        status = "unhealthy"
        response.status_code = 503

    # Log health check
    logger.debug(
        "health_check",
        status=status,
        node_name=config.node_name,
        uptime_seconds=uptime_seconds,
    )

    return HealthResponse(
        status=status,
        node_name=config.node_name,
        timestamp=datetime.now(),
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        capabilities=["repo_read", "repo_search", "markdown_write"],
        checks=checks,
    )
