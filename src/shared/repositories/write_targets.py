"""Write target repository for CRUD operations on the write_targets table."""

import json
from datetime import datetime

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import WriteTargetInfo

logger = get_logger(__name__)


class WriteTargetRepository:
    """Repository for write target registry operations."""

    def __init__(self, db: DatabaseManager):
        """Initialize write target repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(self, target: WriteTargetInfo, repo_id: str) -> WriteTargetInfo:
        """Create a new write target.

        Args:
            target: WriteTargetInfo instance with target data.
            repo_id: Repository ID this target belongs to.

        Returns:
            The created WriteTargetInfo instance.
        """
        now = datetime.utcnow().isoformat()
        extensions_json = json.dumps(target.allowed_extensions)

        await self._db.execute(
            """INSERT INTO write_targets (target_id, repo_id, path, allowed_extensions, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                target.target_id,
                repo_id,
                target.path,
                extensions_json,
                now,
            ),
        )
        logger.info("write_target_created", target_id=target.target_id)
        return target

    async def get(self, target_id: str) -> WriteTargetInfo | None:
        """Get a write target by ID.

        Args:
            target_id: Unique target identifier.

        Returns:
            WriteTargetInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone(
            "SELECT * FROM write_targets WHERE target_id = ?", (target_id,)
        )
        if not row:
            return None
        return self._row_to_target(row)

    async def get_by_path(self, path: str) -> WriteTargetInfo | None:
        """Get a write target by its path.

        Args:
            path: Absolute path to the write target.

        Returns:
            WriteTargetInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone("SELECT * FROM write_targets WHERE path = ?", (path,))
        if not row:
            return None
        return self._row_to_target(row)

    async def list_all(self) -> list[WriteTargetInfo]:
        """List all write targets.

        Returns:
            List of WriteTargetInfo instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall("SELECT * FROM write_targets ORDER BY created_at DESC")
        return [self._row_to_target(row) for row in rows]

    async def list_by_repo(self, repo_id: str) -> list[WriteTargetInfo]:
        """List all write targets for a specific repository.

        Args:
            repo_id: Repository identifier to filter by.

        Returns:
            List of WriteTargetInfo instances for the specified repository.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM write_targets WHERE repo_id = ? ORDER BY created_at DESC",
            (repo_id,),
        )
        return [self._row_to_target(row) for row in rows]

    async def update(self, target: WriteTargetInfo, repo_id: str) -> WriteTargetInfo | None:
        """Update an existing write target.

        Args:
            target: WriteTargetInfo instance with updated data.
            repo_id: Repository ID this target belongs to.

        Returns:
            The updated WriteTargetInfo instance, or None if not found.
        """
        existing = await self.get(target.target_id)
        if not existing:
            return None

        extensions_json = json.dumps(target.allowed_extensions)

        await self._db.execute(
            """UPDATE write_targets SET repo_id = ?, path = ?, allowed_extensions = ?
               WHERE target_id = ?""",
            (
                repo_id,
                target.path,
                extensions_json,
                target.target_id,
            ),
        )
        logger.info("write_target_updated", target_id=target.target_id)
        return target

    async def delete(self, target_id: str) -> bool:
        """Delete a write target.

        Args:
            target_id: Unique target identifier.

        Returns:
            True if target was deleted, False if not found.
        """
        cursor = await self._db.execute(
            "DELETE FROM write_targets WHERE target_id = ?", (target_id,)
        )
        logger.info("write_target_deleted", target_id=target_id)
        return cursor.rowcount > 0

    async def is_path_allowed(self, path: str, extension: str) -> bool:
        """Check if a path and extension are allowed for writing.

        Args:
            path: Absolute path to check.
            extension: File extension (e.g., '.md').

        Returns:
            True if the path has an allowed target with the given extension.
        """
        target = await self.get_by_path(path)
        if not target:
            return False
        return extension in target.allowed_extensions

    def _row_to_target(self, row) -> WriteTargetInfo:
        """Convert database row to WriteTargetInfo.

        Args:
            row: Database row from aiosqlite.

        Returns:
            WriteTargetInfo instance.
        """
        extensions = json.loads(row["allowed_extensions"])
        return WriteTargetInfo(
            target_id=row["target_id"],
            path=row["path"],
            allowed_extensions=extensions,
        )
