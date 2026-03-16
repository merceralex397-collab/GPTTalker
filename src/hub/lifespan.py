"""App lifecycle management for the GPTTalker hub."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.hub.config import get_hub_config
from src.shared.database import initialize_database
from src.shared.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events.

    This lifespan context manager handles:
    1. Initializing logging from config
    2. Initializing database connection
    3. Running migrations
    4. Storing manager references in app state for dependency injection
    5. On shutdown: closing database connections and logging shutdown

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the application during its runtime.
    """
    # Get configuration
    config = get_hub_config()

    # Step 1: Initialize logging
    setup_logging(level=config.log_level, format_type=config.log_format)
    logger.info("hub_starting", config={"host": config.host, "port": config.port})

    # Step 2: Initialize database
    db_manager = await initialize_database()

    # Step 3: Store references in app state for dependency injection
    app.state.db_manager = db_manager
    app.state.config = config

    # Step 4: Initialize HTTP client for hub-to-node communication
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            config.node_client_timeout,
            connect=config.node_client_connect_timeout,
        ),
        limits=httpx.Limits(
            max_connections=config.node_client_pool_max_connections,
            max_keepalive_connections=config.node_client_pool_max_keepalive,
        ),
    )

    logger.info(
        "http_client_initialized",
        timeout=config.node_client_timeout,
        connect_timeout=config.node_client_connect_timeout,
        max_connections=config.node_client_pool_max_connections,
    )

    logger.info("hub_ready", db_path=config.database_url)

    # Yield control to the application
    yield

    # --- Shutdown phase ---

    logger.info("hub_shutting_down")

    # Close HTTP client
    if app.state.http_client is not None:
        await app.state.http_client.aclose()
        logger.info("http_client_closed")

    # Close database connection
    if app.state.db_manager is not None:
        await app.state.db_manager.close()
        logger.info("database_connection_closed")

    logger.info("hub_stopped")
