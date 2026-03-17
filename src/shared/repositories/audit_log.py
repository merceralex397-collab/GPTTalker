"""Audit log repository for CRUD operations on the audit_log table."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import AuditEventType, AuditRecord

logger = get_logger(__name__)


class AuditLogRepository:
    """Repository for audit log operations with full trace context."""

    def __init__(self, db: DatabaseManager):
        """Initialize audit log repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(
        self,
        event_type: AuditEventType,
        actor: str,
        target_type: str,
        action: str,
        outcome: str,
        audit_id: UUID | str | None = None,
        trace_id: str | None = None,
        target_id: str | None = None,
        duration_ms: int | None = None,
        error: str | None = None,
        trace_context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new audit log entry.

        Args:
            event_type: Type of audit event.
            actor: Who triggered this event.
            target_type: Target type (node, repo, doc, service).
            action: Action performed.
            outcome: Outcome (success, failure, rejected).
            audit_id: Optional unique audit identifier (generated if not provided).
            trace_id: Optional trace ID linking to task.
            target_id: Optional target identifier.
            duration_ms: Optional event duration in milliseconds.
            error: Optional error message if failed.
            trace_context: Optional trace context dictionary.
            metadata: Optional metadata dictionary.

        Returns:
            The audit_id as a string.
        """
        now = datetime.utcnow().isoformat()
        audit_id_str = str(audit_id) if audit_id else str(UUID())
        trace_context_json = json.dumps(trace_context or {})
        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """INSERT INTO audit_log (audit_id, trace_id, event_type, actor, target_type, target_id, action, outcome, duration_ms, error, trace_context, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                audit_id_str,
                trace_id,
                event_type.value,
                actor,
                target_type,
                target_id,
                action,
                outcome,
                duration_ms,
                error,
                trace_context_json,
                meta_json,
                now,
            ),
        )
        logger.info(
            "audit_log_created",
            audit_id=audit_id_str,
            event_type=event_type.value,
            actor=actor,
            outcome=outcome,
        )
        return audit_id_str

    async def get(self, audit_id: str | UUID) -> AuditRecord | None:
        """Get an audit entry by ID.

        Args:
            audit_id: Unique audit identifier.

        Returns:
            AuditRecord instance if found, None otherwise.
        """
        audit_id_str = str(audit_id)
        row = await self._db.fetchone("SELECT * FROM audit_log WHERE audit_id = ?", (audit_id_str,))
        if not row:
            return None
        return self._row_to_record(row)

    async def list_all(self, limit: int = 100) -> list[AuditRecord]:
        """List all audit log entries.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of AuditRecord instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [self._row_to_record(row) for row in rows]

    async def list_by_trace(self, trace_id: str) -> list[AuditRecord]:
        """Get all audit entries with a specific trace ID.

        Args:
            trace_id: Trace identifier to search by.

        Returns:
            List of AuditRecord instances with the specified trace ID.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM audit_log WHERE trace_id = ? ORDER BY created_at DESC",
            (trace_id,),
        )
        return [self._row_to_record(row) for row in rows]

    async def list_by_event_type(
        self, event_type: AuditEventType, limit: int = 100
    ) -> list[AuditRecord]:
        """List all audit entries for a specific event type.

        Args:
            event_type: AuditEventType to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of AuditRecord instances for the specified event type.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM audit_log WHERE event_type = ? ORDER BY created_at DESC LIMIT ?",
            (event_type.value, limit),
        )
        return [self._row_to_record(row) for row in rows]

    async def list_by_actor(self, actor: str, limit: int = 100) -> list[AuditRecord]:
        """List all audit entries for a specific actor.

        Args:
            actor: Actor identifier to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of AuditRecord instances for the specified actor.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM audit_log WHERE actor = ? ORDER BY created_at DESC LIMIT ?",
            (actor, limit),
        )
        return [self._row_to_record(row) for row in rows]

    async def list_by_target(
        self, target_type: str, target_id: str, limit: int = 100
    ) -> list[AuditRecord]:
        """List all audit entries for a specific target.

        Args:
            target_type: Target type to filter by.
            target_id: Target identifier to filter by.
            limit: Maximum number of records to return.

        Returns:
            List of AuditRecord instances for the specified target.
        """
        rows = await self._db.fetchall(
            """SELECT * FROM audit_log
               WHERE target_type = ? AND target_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (target_type, target_id, limit),
        )
        return [self._row_to_record(row) for row in rows]

    async def list_by_timerange(
        self,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """List audit entries within a time range.

        Args:
            start: Start datetime.
            end: End datetime.
            limit: Maximum number of records to return.

        Returns:
            List of AuditRecord instances within the specified time range.
        """
        rows = await self._db.fetchall(
            """SELECT * FROM audit_log
               WHERE created_at >= ? AND created_at <= ?
               ORDER BY created_at DESC LIMIT ?""",
            (start.isoformat(), end.isoformat(), limit),
        )
        return [self._row_to_record(row) for row in rows]

    async def delete(self, audit_id: str | UUID) -> bool:
        """Delete an audit entry.

        Args:
            audit_id: Unique audit identifier.

        Returns:
            True if entry was deleted, False if not found.
        """
        audit_id_str = str(audit_id)
        cursor = await self._db.execute("DELETE FROM audit_log WHERE audit_id = ?", (audit_id_str,))
        logger.info("audit_log_deleted", audit_id=audit_id_str)
        return cursor.rowcount > 0

    async def count_by_event_type(self) -> dict[str, int]:
        """Get count of audit entries grouped by event type.

        Returns:
            Dictionary mapping event_type to count.
        """
        rows = await self._db.fetchall(
            "SELECT event_type, COUNT(*) as count FROM audit_log GROUP BY event_type"
        )
        return {row["event_type"]: row["count"] for row in rows}

    async def count_by_outcome(self) -> dict[str, int]:
        """Get count of audit entries grouped by outcome.

        Returns:
            Dictionary mapping outcome to count.
        """
        rows = await self._db.fetchall(
            "SELECT outcome, COUNT(*) as count FROM audit_log GROUP BY outcome"
        )
        return {row["outcome"]: row["count"] for row in rows}

    def _row_to_record(self, row) -> AuditRecord:
        """Convert database row to AuditRecord.

        Args:
            row: Database row from aiosqlite.

        Returns:
            AuditRecord instance.
        """
        trace_context = json.loads(row["trace_context"]) if row["trace_context"] else {}
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        return AuditRecord(
            audit_id=UUID(row["audit_id"]),
            trace_id=row["trace_id"],
            event_type=AuditEventType(row["event_type"]),
            actor=row["actor"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            action=row["action"],
            outcome=row["outcome"],
            duration_ms=row["duration_ms"],
            error=row["error"],
            trace_context=trace_context,
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=metadata,
        )
