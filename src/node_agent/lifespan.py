"""App lifecycle management for the GPTTalker node agent."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.node_agent.config import get_node_agent_config
from src.node_agent.executor import OperationExecutor
from src.shared.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events.

    This lifespan context manager handles:
    1. Initializing logging from config
    2. Validating and loading node agent config
    3. Initializing OperationExecutor with allowed paths
    4. Storing config and executor in app state for dependency injection
    5. On shutdown: logging termination

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the application during its runtime.
    """
    # Step 1: Get configuration
    config = get_node_agent_config()

    # Step 2: Initialize logging
    setup_logging(level="INFO", format_type="text")
    logger.info(
        "node_agent_starting",
        node_name=config.node_name,
        hub_url=config.hub_url,
    )

    # Step 3: Initialize OperationExecutor with allowed paths
    allowed_paths = config.allowed_repos + config.allowed_write_targets
    executor = OperationExecutor(allowed_paths=allowed_paths)
    logger.info(
        "executor_initialized",
        allowed_repos_count=len(config.allowed_repos),
        allowed_write_targets_count=len(config.allowed_write_targets),
    )

    # Step 4: Store references in app state for dependency injection
    app.state.config = config
    app.state.executor = executor
    app.state.startup_time = __import__("time").time()

    logger.info(
        "node_agent_ready",
        node_name=config.node_name,
        capabilities=["repo_read", "repo_search", "markdown_write"],
    )

    # Yield control to the application
    yield

    # --- Shutdown phase ---

    logger.info("node_agent_shutting_down", node_name=config.node_name)

    logger.info("node_agent_stopped")
