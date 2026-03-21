"""Task repository for CRUD operations on the tasks table."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import TaskOutcome, TaskRecord

logger = get_logger(__name__)


class TaskRepository:
    """Repository for task history and audit operations."""

    def __init__(self, db: DatabaseManager):
        """Initialize task repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(
        self,
        task_id: UUID | str,
        tool_name: str,
        caller: str,
        outcome: TaskOutcome,
        duration_ms: int,
        trace_id: str | None = None,
        target_node: str | None = None,
        target_repo: str | None = None,
        started_at: datetime | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new task record.

        Args:
            task_id: Unique task identifier (UUID or string).
            tool_name: Name of the tool that was called.
            caller: Caller identifier.
            outcome: Task outcome status.
            duration_ms: Duration in milliseconds.
            trace_id: Optional trace ID for request tracking.
            target_node: Optional target node identifier.
            target_repo: Optional target repo identifier.
            started_at: Optional task start time.
            error: Optional error message if failed.
            metadata: Optional metadata dictionary.

        Returns:
            The task_id as a string.
        """
        now = datetime.utcnow().isoformat()
        task_id_str = str(task_id)
        started_iso = started_at.isoformat() if started_at else None
        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """INSERT INTO tasks (task_id, trace_id, tool_name, caller, target_node, target_repo, outcome, duration_ms, started_at, completed_at, error, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id_str,
                trace_id,
                tool_name,
                caller,
                target_node,
                target_repo,
                outcome.value,
                duration_ms,
                started_iso,
                now,
                error,
                meta_json,
                now,
            ),
        )
        logger.info("task_created", task_id=task_id_str, tool_name=tool_name, outcome=outcome.value)
        return task_id_str

    async def get(self, task_id: str | UUID) -> TaskRecord | None:
        """Get a task by ID.

        Args:
            task_id: Unique task identifier.

        Returns:
            TaskRecord instance if found, None otherwise.
        """
        task_id_str = str(task_id)
        row = await self._db.fetchone("SELECT * FROM tasks WHERE task_id = ?", (task_id_str,))
        if not row:
            return None
        return self._row_to_task(row)

    async def get_by_trace(self, trace_id: str) -> list[TaskRecord]:
        """Get all tasks with a specific trace ID.

        Args:
            trace_id: Trace identifier to search by.

        Returns:
            List of TaskRecord instances with the specified trace ID.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM tasks WHERE trace_id = ? ORDER BY created_at DESC",
            (trace_id,),
        )
        return [self._row_to_task(row) for row in rows]

    async def list_all(self, limit: int = 100) -> list[TaskRecord]:
        """List all tasks.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of TaskRecord instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [self._row_to_task(row) for row in rows]

    async def list_by_outcome(self, outcome: TaskOutcome, limit: int = 100) -> list[TaskRecord]:
        """List all tasks with a specific outcome.

        Args:
            outcome: TaskOutcome to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of TaskRecord instances with the specified outcome.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM tasks WHERE outcome = ? ORDER BY created_at DESC LIMIT ?",
            (outcome.value, limit),
        )
        return [self._row_to_task(row) for row in rows]

    async def list_by_tool(self, tool_name: str, limit: int = 100) -> list[TaskRecord]:
        """List all tasks for a specific tool.

        Args:
            tool_name: Tool name to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of TaskRecord instances for the specified tool.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM tasks WHERE tool_name = ? ORDER BY created_at DESC LIMIT ?",
            (tool_name, limit),
        )
        return [self._row_to_task(row) for row in rows]

    async def list_recent(self, hours: int = 24, limit: int = 100) -> list[TaskRecord]:
        """List recent tasks within a time window.

        Args:
            hours: Number of hours to look back.
            limit: Maximum number of records to return.

        Returns:
            List of recent TaskRecord instances.
        """
        rows = await self._db.fetchall(
            """SELECT * FROM tasks
               WHERE created_at >= datetime('now', ?)
               ORDER BY created_at DESC LIMIT ?""",
            (f"-{hours} hours", limit),
        )
        return [self._row_to_task(row) for row in rows]

    async def delete(self, task_id: str | UUID) -> bool:
        """Delete a task record.

        Args:
            task_id: Unique task identifier.

        Returns:
            True if task was deleted, False if not found.
        """
        task_id_str = str(task_id)
        cursor = await self._db.execute("DELETE FROM tasks WHERE task_id = ?", (task_id_str,))
        logger.info("task_deleted", task_id=task_id_str)
        return cursor.rowcount > 0

    async def count_by_outcome(self) -> dict[str, int]:
        """Get count of tasks grouped by outcome.

        Returns:
            Dictionary mapping outcome to count.
        """
        rows = await self._db.fetchall(
            "SELECT outcome, COUNT(*) as count FROM tasks GROUP BY outcome"
        )
        return {row["outcome"]: row["count"] for row in rows}

    def _row_to_task(self, row) -> TaskRecord:
        """Convert database row to TaskRecord.

        Args:
            row: Database row from aiosqlite.

        Returns:
            TaskRecord instance.
        """
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        # Handle both UUID and string task_ids
        task_id_value = row["task_id"]
        try:
            task_id = UUID(task_id_value)
        except ValueError:
            # Not a valid UUID, use as string
            task_id = task_id_value

        return TaskRecord(
            task_id=task_id,
            trace_id=row["trace_id"],
            tool_name=row["tool_name"],
            caller=row["caller"],
            target_node=row["target_node"],
            target_repo=row["target_repo"],
            outcome=TaskOutcome(row["outcome"]),
            duration_ms=row["duration_ms"],
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            error=row["error"],
            metadata=metadata,
        )
