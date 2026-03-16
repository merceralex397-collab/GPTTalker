"""LLM service repository for CRUD operations on the llm_services table."""

import json
from datetime import datetime
from typing import Any

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import LLMServiceInfo, LLMServiceType

logger = get_logger(__name__)


class LLMServiceRepository:
    """Repository for LLM service registry operations."""

    def __init__(self, db: DatabaseManager):
        """Initialize LLM service repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(
        self, service: LLMServiceInfo, metadata: dict[str, Any] | None = None
    ) -> LLMServiceInfo:
        """Create a new LLM service.

        Args:
            service: LLMServiceInfo instance with service data.
            metadata: Optional metadata dictionary to store as JSON.

        Returns:
            The created LLMServiceInfo instance.
        """
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """INSERT INTO llm_services (service_id, name, type, endpoint, api_key, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                service.service_id,
                service.name,
                service.type.value,
                service.endpoint,
                service.api_key,
                now,
                meta_json,
            ),
        )
        logger.info("llm_service_created", service_id=service.service_id)
        return service

    async def get(self, service_id: str) -> LLMServiceInfo | None:
        """Get an LLM service by ID.

        Args:
            service_id: Unique service identifier.

        Returns:
            LLMServiceInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone(
            "SELECT * FROM llm_services WHERE service_id = ?", (service_id,)
        )
        if not row:
            return None
        return self._row_to_service(row)

    async def get_by_name(self, name: str) -> LLMServiceInfo | None:
        """Get an LLM service by its name.

        Args:
            name: Human-readable service name.

        Returns:
            LLMServiceInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone("SELECT * FROM llm_services WHERE name = ?", (name,))
        if not row:
            return None
        return self._row_to_service(row)

    async def list_all(self) -> list[LLMServiceInfo]:
        """List all LLM services.

        Returns:
            List of LLMServiceInfo instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall("SELECT * FROM llm_services ORDER BY created_at DESC")
        return [self._row_to_service(row) for row in rows]

    async def list_by_type(self, service_type: LLMServiceType) -> list[LLMServiceInfo]:
        """List all LLM services of a specific type.

        Args:
            service_type: LLMServiceType to filter by.

        Returns:
            List of LLMServiceInfo instances of the specified type.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM llm_services WHERE type = ? ORDER BY created_at DESC",
            (service_type.value,),
        )
        return [self._row_to_service(row) for row in rows]

    async def update(
        self, service: LLMServiceInfo, metadata: dict[str, Any] | None = None
    ) -> LLMServiceInfo | None:
        """Update an existing LLM service.

        Args:
            service: LLMServiceInfo instance with updated data.
            metadata: Optional metadata dictionary to store as JSON.

        Returns:
            The updated LLMServiceInfo instance, or None if not found.
        """
        existing = await self.get(service.service_id)
        if not existing:
            return None

        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """UPDATE llm_services SET name = ?, type = ?, endpoint = ?, api_key = ?, metadata = ?
               WHERE service_id = ?""",
            (
                service.name,
                service.type.value,
                service.endpoint,
                service.api_key,
                meta_json,
                service.service_id,
            ),
        )
        logger.info("llm_service_updated", service_id=service.service_id)
        return service

    async def delete(self, service_id: str) -> bool:
        """Delete an LLM service.

        Args:
            service_id: Unique service identifier.

        Returns:
            True if service was deleted, False if not found.
        """
        cursor = await self._db.execute(
            "DELETE FROM llm_services WHERE service_id = ?", (service_id,)
        )
        logger.info("llm_service_deleted", service_id=service_id)
        return cursor.rowcount > 0

    def _row_to_service(self, row) -> LLMServiceInfo:
        """Convert database row to LLMServiceInfo.

        Args:
            row: Database row from aiosqlite.

        Returns:
            LLMServiceInfo instance.
        """
        return LLMServiceInfo(
            service_id=row["service_id"],
            name=row["name"],
            type=LLMServiceType(row["type"]),
            endpoint=row["endpoint"],
            api_key=row["api_key"],
        )
