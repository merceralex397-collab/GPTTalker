"""Issue repository for CRUD operations on the issues table."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import IssueRecord, IssueStatus

logger = get_logger(__name__)


class IssueRepository:
    """Repository for known issue tracking operations."""

    def __init__(self, db: DatabaseManager):
        """Initialize issue repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(
        self,
        issue_id: UUID | str,
        repo_id: str,
        title: str,
        description: str,
        status: IssueStatus = IssueStatus.OPEN,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new issue record.

        Args:
            issue_id: Unique issue identifier (UUID or string).
            repo_id: Repository this issue belongs to.
            title: Issue title.
            description: Issue description.
            status: Current issue status.
            metadata: Optional metadata dictionary.

        Returns:
            The issue_id as a string.
        """
        now = datetime.utcnow().isoformat()
        issue_id_str = str(issue_id)
        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """INSERT INTO issues (issue_id, repo_id, title, description, status, created_at, updated_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                issue_id_str,
                repo_id,
                title,
                description,
                status.value,
                now,
                now,
                meta_json,
            ),
        )
        logger.info("issue_created", issue_id=issue_id_str, repo_id=repo_id)
        return issue_id_str

    async def get(self, issue_id: str | UUID) -> IssueRecord | None:
        """Get an issue by ID.

        Args:
            issue_id: Unique issue identifier.

        Returns:
            IssueRecord instance if found, None otherwise.
        """
        issue_id_str = str(issue_id)
        row = await self._db.fetchone("SELECT * FROM issues WHERE issue_id = ?", (issue_id_str,))
        if not row:
            return None
        return self._row_to_issue(row)

    async def list_all(self, limit: int = 100) -> list[IssueRecord]:
        """List all issues.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of IssueRecord instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall(
            "SELECT * FROM issues ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [self._row_to_issue(row) for row in rows]

    async def list_by_repo(self, repo_id: str, limit: int = 100) -> list[IssueRecord]:
        """List all issues for a specific repository.

        Args:
            repo_id: Repository identifier to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of IssueRecord instances for the specified repository.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM issues WHERE repo_id = ? ORDER BY created_at DESC LIMIT ?",
            (repo_id, limit),
        )
        return [self._row_to_issue(row) for row in rows]

    async def list_by_status(self, status: IssueStatus, limit: int = 100) -> list[IssueRecord]:
        """List all issues with a specific status.

        Args:
            status: IssueStatus to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of IssueRecord instances with the specified status.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM issues WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status.value, limit),
        )
        return [self._row_to_issue(row) for row in rows]

    async def list_open(self, limit: int = 100) -> list[IssueRecord]:
        """List all open issues.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of open IssueRecord instances.
        """
        return await self.list_by_status(IssueStatus.OPEN, limit)

    async def update(
        self,
        issue_id: str | UUID,
        title: str | None = None,
        description: str | None = None,
        status: IssueStatus | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IssueRecord | None:
        """Update an existing issue.

        Args:
            issue_id: Unique issue identifier.
            title: Optional new title.
            description: Optional new description.
            status: Optional new status.
            metadata: Optional new metadata.

        Returns:
            The updated IssueRecord instance, or None if not found.
        """
        existing = await self.get(issue_id)
        if not existing:
            return None

        now = datetime.utcnow().isoformat()
        new_title = title if title is not None else existing.title
        new_description = description if description is not None else existing.description
        new_status = status if status is not None else existing.status
        meta_json = json.dumps(metadata or existing.metadata)

        await self._db.execute(
            """UPDATE issues SET title = ?, description = ?, status = ?, updated_at = ?, metadata = ?
               WHERE issue_id = ?""",
            (
                new_title,
                new_description,
                new_status.value,
                now,
                meta_json,
                str(issue_id),
            ),
        )
        logger.info("issue_updated", issue_id=str(issue_id))
        return await self.get(issue_id)

    async def delete(self, issue_id: str | UUID) -> bool:
        """Delete an issue.

        Args:
            issue_id: Unique issue identifier.

        Returns:
            True if issue was deleted, False if not found.
        """
        issue_id_str = str(issue_id)
        cursor = await self._db.execute("DELETE FROM issues WHERE issue_id = ?", (issue_id_str,))
        logger.info("issue_deleted", issue_id=issue_id_str)
        return cursor.rowcount > 0

    async def count_by_status(self) -> dict[str, int]:
        """Get count of issues grouped by status.

        Returns:
            Dictionary mapping status to count.
        """
        rows = await self._db.fetchall(
            "SELECT status, COUNT(*) as count FROM issues GROUP BY status"
        )
        return {row["status"]: row["count"] for row in rows}

    async def list_recurring(self, min_count: int = 2) -> list[dict[str, Any]]:
        """Find issues that appear to be recurring based on title similarity.

        Args:
            min_count: Minimum number of similar titles to consider recurring.

        Returns:
            List of dictionaries with title and count.
        """
        # This is a simplified implementation - in production, you'd want
        # more sophisticated matching (fuzzy search, embeddings, etc.)
        rows = await self._db.fetchall(
            """SELECT title, COUNT(*) as count
               FROM issues
               GROUP BY title
               HAVING count >= ?
               ORDER BY count DESC""",
            (min_count,),
        )
        return [{"title": row["title"], "count": row["count"]} for row in rows]

    def _row_to_issue(self, row) -> IssueRecord:
        """Convert database row to IssueRecord.

        Args:
            row: Database row from aiosqlite.

        Returns:
            IssueRecord instance.
        """
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        return IssueRecord(
            issue_id=UUID(row["issue_id"]),
            repo_id=row["repo_id"],
            title=row["title"],
            description=row["description"],
            status=IssueStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            metadata=metadata,
        )
