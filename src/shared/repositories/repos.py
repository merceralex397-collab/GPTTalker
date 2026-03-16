"""Repository repository for CRUD operations on the repos table."""

import json
from datetime import datetime
from typing import Any

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import RepoInfo

logger = get_logger(__name__)


class RepoRepository:
    """Repository for repository registry operations."""

    def __init__(self, db: DatabaseManager):
        """Initialize repo repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(self, repo: RepoInfo, metadata: dict[str, Any] | None = None) -> RepoInfo:
        """Create a new repository.

        Args:
            repo: RepoInfo instance with repository data.
            metadata: Optional metadata dictionary to store as JSON.

        Returns:
            The created RepoInfo instance.
        """
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """INSERT INTO repos (repo_id, node_id, name, path, is_indexed, indexed_at, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                repo.repo_id,
                repo.node_id,
                repo.name,
                repo.path,
                1 if repo.is_indexed else 0,
                None,
                now,
                meta_json,
            ),
        )
        logger.info("repo_created", repo_id=repo.repo_id)
        return repo

    async def get(self, repo_id: str) -> RepoInfo | None:
        """Get a repository by ID.

        Args:
            repo_id: Unique repository identifier.

        Returns:
            RepoInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone("SELECT * FROM repos WHERE repo_id = ?", (repo_id,))
        if not row:
            return None
        return self._row_to_repo(row)

    async def get_by_path(self, path: str) -> RepoInfo | None:
        """Get a repository by its path.

        Args:
            path: Absolute path to the repository.

        Returns:
            RepoInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone("SELECT * FROM repos WHERE path = ?", (path,))
        if not row:
            return None
        return self._row_to_repo(row)

    async def list_all(self) -> list[RepoInfo]:
        """List all repositories.

        Returns:
            List of RepoInfo instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall("SELECT * FROM repos ORDER BY created_at DESC")
        return [self._row_to_repo(row) for row in rows]

    async def list_by_node(self, node_id: str) -> list[RepoInfo]:
        """List all repositories on a specific node.

        Args:
            node_id: Node identifier to filter by.

        Returns:
            List of RepoInfo instances on the specified node.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM repos WHERE node_id = ? ORDER BY created_at DESC",
            (node_id,),
        )
        return [self._row_to_repo(row) for row in rows]

    async def list_indexed(self) -> list[RepoInfo]:
        """List all indexed repositories.

        Returns:
            List of RepoInfo instances that are marked as indexed.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM repos WHERE is_indexed = 1 ORDER BY indexed_at DESC"
        )
        return [self._row_to_repo(row) for row in rows]

    async def update(
        self, repo: RepoInfo, metadata: dict[str, Any] | None = None
    ) -> RepoInfo | None:
        """Update an existing repository.

        Args:
            repo: RepoInfo instance with updated data.
            metadata: Optional metadata dictionary to store as JSON.

        Returns:
            The updated RepoInfo instance, or None if not found.
        """
        existing = await self.get(repo.repo_id)
        if not existing:
            return None

        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """UPDATE repos SET node_id = ?, name = ?, path = ?, is_indexed = ?, indexed_at = ?, metadata = ?
               WHERE repo_id = ?""",
            (
                repo.node_id,
                repo.name,
                repo.path,
                1 if repo.is_indexed else 0,
                repo.is_indexed and repo.repo_id,
                meta_json,
                repo.repo_id,
            ),
        )
        logger.info("repo_updated", repo_id=repo.repo_id)
        return repo

    async def delete(self, repo_id: str) -> bool:
        """Delete a repository.

        Args:
            repo_id: Unique repository identifier.

        Returns:
            True if repository was deleted, False if not found.
        """
        cursor = await self._db.execute("DELETE FROM repos WHERE repo_id = ?", (repo_id,))
        logger.info("repo_deleted", repo_id=repo_id)
        return cursor.rowcount > 0

    async def mark_indexed(self, repo_id: str) -> bool:
        """Mark a repository as indexed.

        Args:
            repo_id: Unique repository identifier.

        Returns:
            True if updated, False if repository not found.
        """
        now = datetime.utcnow().isoformat()
        cursor = await self._db.execute(
            "UPDATE repos SET is_indexed = 1, indexed_at = ? WHERE repo_id = ?",
            (now, repo_id),
        )
        logger.info("repo_marked_indexed", repo_id=repo_id)
        return cursor.rowcount > 0

    async def mark_unindexed(self, repo_id: str) -> bool:
        """Mark a repository as not indexed.

        Args:
            repo_id: Unique repository identifier.

        Returns:
            True if updated, False if repository not found.
        """
        cursor = await self._db.execute(
            "UPDATE repos SET is_indexed = 0, indexed_at = NULL WHERE repo_id = ?",
            (repo_id,),
        )
        logger.info("repo_marked_unindexed", repo_id=repo_id)
        return cursor.rowcount > 0

    def _row_to_repo(self, row) -> RepoInfo:
        """Convert database row to RepoInfo.

        Args:
            row: Database row from aiosqlite.

        Returns:
            RepoInfo instance.
        """
        return RepoInfo(
            repo_id=row["repo_id"],
            name=row["name"],
            path=row["path"],
            node_id=row["node_id"],
            is_indexed=bool(row["is_indexed"]),
        )
