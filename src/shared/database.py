"""Async SQLite connection management for GPTTalker."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from .config import SharedConfig, get_shared_config
from .logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages async SQLite connections for GPTTalker."""

    def __init__(self, config: SharedConfig | None = None):
        """Initialize database manager.

        Args:
            config: Optional SharedConfig instance. If not provided, loads from environment.
        """
        self._config = config or get_shared_config()
        self._db_path = self._config.database_path
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database connection and run migrations.

        Creates the database directory if it doesn't exist and establishes
        a connection with row factory set for dict-like access.
        """
        # Ensure directory exists
        db_path = Path(self._db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row
        # Set isolation_level to '' (empty string) to disable autocommit
        # This requires explicit BEGIN/COMMIT/ROLLBACK for transactions
        self._connection.isolation_level = ""

        logger.info("database_initialized", db_path=str(self._db_path))

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("database_closed")

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the current connection.

        Returns:
            The active SQLite connection.

        Raises:
            RuntimeError: If database has not been initialized.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._connection

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Context manager for database transactions.

        Yields:
            A connection that can be used to execute queries within a transaction.

        Example:
            async with db.transaction() as conn:
                await conn.execute("INSERT INTO ...", ...)
                await conn.execute("UPDATE ...", ...)
        """
        # Begin explicit transaction
        await self.connection.execute("BEGIN")
        try:
            yield self.connection
            await self.connection.execute("COMMIT")
        except Exception:
            await self.connection.execute("ROLLBACK")
            raise

    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query, commit, and return cursor.

        Args:
            query: SQL query string.
            parameters: Tuple of query parameters.

        Returns:
            Cursor object with query results.
        """
        cursor = await self.connection.execute(query, parameters)
        await self.connection.commit()
        return cursor

    async def executemany(self, query: str, parameters: list) -> aiosqlite.Cursor:
        """Execute a query with multiple parameter sets, commit, and return cursor.

        Args:
            query: SQL query string.
            parameters: List of parameter tuples.

        Returns:
            Cursor object with query results.
        """
        cursor = await self.connection.executemany(query, parameters)
        await self.connection.commit()
        return cursor

    async def fetchone(self, query: str, parameters: tuple = ()) -> aiosqlite.Row | None:
        """Execute query and fetch one result.

        Args:
            query: SQL query string.
            parameters: Tuple of query parameters.

        Returns:
            Single row from query results, or None if no results.
        """
        async with self.connection.execute(query, parameters) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, query: str, parameters: tuple = ()) -> list[aiosqlite.Row]:
        """Execute query and fetch all results.

        Args:
            query: SQL query string.
            parameters: Tuple of query parameters.

        Returns:
            List of all rows from query results.
        """
        async with self.connection.execute(query, parameters) as cursor:
            return await cursor.fetchall()


# Global instance
_db_manager: DatabaseManager | None = None


def get_db_manager(config: SharedConfig | None = None) -> DatabaseManager:
    """Get or create the global database manager.

    Args:
        config: Optional SharedConfig instance.

    Returns:
        The global DatabaseManager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config)
    return _db_manager


async def initialize_database(config: SharedConfig | None = None) -> DatabaseManager:
    """Initialize the database and run migrations.

    Args:
        config: Optional SharedConfig instance.

    Returns:
        The initialized DatabaseManager instance.
    """
    manager = get_db_manager(config)
    await manager.initialize()

    from .migrations import run_migrations

    await run_migrations(manager)

    return manager


async def get_connection() -> aiosqlite.Connection:
    """Get a database connection for direct access.

    This is a convenience function that returns the connection
    from the global database manager.

    Returns:
        The active SQLite connection.

    Raises:
        RuntimeError: If database has not been initialized.
    """
    manager = get_db_manager()
    return manager.connection
