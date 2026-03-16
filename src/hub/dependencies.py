"""Dependency injection providers for the GPTTalker hub."""

from collections.abc import AsyncGenerator
from typing import Any

import aiosqlite
from fastapi import Request

from src.hub.config import HubConfig, get_hub_config
from src.shared.database import DatabaseManager
from src.shared.logging import get_logger

# Logger instance for this module
logger = get_logger(__name__)


async def get_db(request: Request) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get database connection from app state.

    This dependency provides a database connection that is scoped to the
    current request. The connection is retrieved from app state where
    it is stored by the lifespan handler.

    Args:
        request: The current FastAPI request.

    Yields:
        An aiosqlite connection for database operations.

    Raises:
        RuntimeError: If database is not initialized.
    """
    # Get database from app state (set by lifespan)
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")

    yield db_manager.connection


async def get_db_manager_dep(request: Request) -> DatabaseManager:
    """Get the database manager instance.

    Args:
        request: The current FastAPI request.

    Returns:
        The DatabaseManager instance from app state.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return db_manager


def get_config() -> HubConfig:
    """Get hub configuration.

    Returns:
        HubConfig instance with environment overrides.
    """
    return get_hub_config()


def get_hub_logger() -> Any:
    """Get a logger for hub operations.

    Returns:
        Logger instance for hub-specific logging.
    """
    return get_logger("gpttalker-hub")


async def check_database_health(request: Request) -> dict[str, Any]:
    """Check database connectivity.

    This is a dependency that can be used to verify database
    connectivity for health checks.

    Args:
        request: The current FastAPI request.

    Returns:
        Dict with database health status.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        return {"status": "uninitialized", "connected": False}

    try:
        # Try a simple query to verify connectivity
        await db_manager.connection.execute("SELECT 1")
        return {"status": "healthy", "connected": True}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"status": "unhealthy", "connected": False, "error": str(e)}
