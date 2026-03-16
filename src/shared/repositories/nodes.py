"""Node repository for CRUD operations on the nodes table."""

import json
from datetime import datetime
from typing import Any

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import NodeInfo, NodeStatus
from ..schemas import NodeHealthStatus

logger = get_logger(__name__)


class NodeRepository:
    """Repository for node registry operations."""

    def __init__(self, db: DatabaseManager):
        """Initialize node repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self._db = db

    async def create(self, node: NodeInfo, metadata: dict[str, Any] | None = None) -> NodeInfo:
        """Create a new node.

        Args:
            node: NodeInfo instance with node data.
            metadata: Optional metadata dictionary to store as JSON.

        Returns:
            The created NodeInfo instance.
        """
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """INSERT INTO nodes (node_id, name, hostname, status, last_seen, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                node.node_id,
                node.name,
                node.hostname,
                node.status.value,
                node.last_seen.isoformat() if node.last_seen else None,
                now,
                meta_json,
            ),
        )
        logger.info("node_created", node_id=node.node_id)
        return node

    async def get(self, node_id: str) -> NodeInfo | None:
        """Get a node by ID.

        Args:
            node_id: Unique node identifier.

        Returns:
            NodeInfo instance if found, None otherwise.
        """
        row = await self._db.fetchone("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
        if not row:
            return None
        return self._row_to_node(row)

    async def list_all(self) -> list[NodeInfo]:
        """List all nodes.

        Returns:
            List of NodeInfo instances ordered by creation date (newest first).
        """
        rows = await self._db.fetchall("SELECT * FROM nodes ORDER BY created_at DESC")
        return [self._row_to_node(row) for row in rows]

    async def list_by_status(self, status: NodeStatus) -> list[NodeInfo]:
        """List all nodes with a specific status.

        Args:
            status: NodeStatus to filter by.

        Returns:
            List of NodeInfo instances with the specified status.
        """
        rows = await self._db.fetchall(
            "SELECT * FROM nodes WHERE status = ? ORDER BY created_at DESC",
            (status.value,),
        )
        return [self._row_to_node(row) for row in rows]

    async def update(
        self, node: NodeInfo, metadata: dict[str, Any] | None = None
    ) -> NodeInfo | None:
        """Update an existing node.

        Args:
            node: NodeInfo instance with updated data.
            metadata: Optional metadata dictionary to store as JSON.

        Returns:
            The updated NodeInfo instance, or None if not found.
        """
        existing = await self.get(node.node_id)
        if not existing:
            return None

        meta_json = json.dumps(metadata or {})

        await self._db.execute(
            """UPDATE nodes SET name = ?, hostname = ?, status = ?, last_seen = ?, metadata = ?
               WHERE node_id = ?""",
            (
                node.name,
                node.hostname,
                node.status.value,
                node.last_seen.isoformat() if node.last_seen else None,
                meta_json,
                node.node_id,
            ),
        )
        logger.info("node_updated", node_id=node.node_id)
        return node

    async def delete(self, node_id: str) -> bool:
        """Delete a node.

        Args:
            node_id: Unique node identifier.

        Returns:
            True if node was deleted, False if not found.
        """
        cursor = await self._db.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
        logger.info("node_deleted", node_id=node_id)
        return cursor.rowcount > 0

    async def update_status(self, node_id: str, status: NodeStatus) -> bool:
        """Update node status.

        Args:
            node_id: Unique node identifier.
            status: New NodeStatus value.

        Returns:
            True if status was updated, False if node not found.
        """
        await self._db.execute(
            "UPDATE nodes SET status = ?, last_seen = ? WHERE node_id = ?",
            (status.value, datetime.utcnow().isoformat(), node_id),
        )
        logger.info("node_status_updated", node_id=node_id, status=status.value)
        return True

    async def update_last_seen(self, node_id: str) -> bool:
        """Update node's last_seen timestamp to current time.

        Args:
            node_id: Unique node identifier.

        Returns:
            True if updated, False if node not found.
        """
        cursor = await self._db.execute(
            "UPDATE nodes SET last_seen = ? WHERE node_id = ?",
            (datetime.utcnow().isoformat(), node_id),
        )
        return cursor.rowcount > 0

    async def get_health(self, node_id: str) -> dict[str, Any] | None:
        """Get health metadata for a node.

        Args:
            node_id: Unique node identifier.

        Returns:
            Dictionary with health metadata, or None if not found.
        """
        row = await self._db.fetchone(
            """SELECT health_status, health_latency_ms, health_error,
                      health_check_count, consecutive_failures,
                      last_health_check, last_health_attempt
               FROM nodes WHERE node_id = ?""",
            (node_id,),
        )
        if not row:
            return None

        return {
            "health_status": NodeHealthStatus(row["health_status"])
            if row["health_status"]
            else NodeHealthStatus.UNKNOWN,
            "health_latency_ms": row["health_latency_ms"],
            "health_error": row["health_error"],
            "health_check_count": row["health_check_count"] or 0,
            "consecutive_failures": row["consecutive_failures"] or 0,
            "last_health_check": datetime.fromisoformat(row["last_health_check"])
            if row["last_health_check"]
            else None,
            "last_health_attempt": datetime.fromisoformat(row["last_health_attempt"])
            if row["last_health_attempt"]
            else None,
        }

    async def update_health(
        self,
        node_id: str,
        status: NodeHealthStatus,
        latency_ms: int | None = None,
        error: str | None = None,
        check_count: int | None = None,
        consecutive_failures: int | None = None,
        last_check: datetime | None = None,
        last_attempt: datetime | None = None,
    ) -> bool:
        """Update health metadata for a node.

        Args:
            node_id: Unique node identifier.
            status: Health status value.
            latency_ms: Response latency in milliseconds.
            error: Error message if any.
            check_count: Total health check count.
            consecutive_failures: Number of consecutive failures.
            last_check: Last successful health check time.
            last_attempt: Last health check attempt time.

        Returns:
            True if updated, False if node not found.
        """
        # Get current values if not provided
        if check_count is None or consecutive_failures is None:
            current = await self.get_health(node_id)
            if current:
                check_count = (
                    check_count if check_count is not None else current.get("health_check_count", 0)
                )
                consecutive_failures = (
                    consecutive_failures
                    if consecutive_failures is not None
                    else current.get("consecutive_failures", 0)
                )

        await self._db.execute(
            """UPDATE nodes SET
               health_status = ?,
               health_latency_ms = ?,
               health_error = ?,
               health_check_count = ?,
               consecutive_failures = ?,
               last_health_check = ?,
               last_health_attempt = ?
               WHERE node_id = ?""",
            (
                status.value,
                latency_ms,
                error,
                check_count,
                consecutive_failures,
                last_check.isoformat() if last_check else None,
                last_attempt.isoformat() if last_attempt else None,
                node_id,
            ),
        )
        logger.info(
            "node_health_updated",
            node_id=node_id,
            status=status.value,
            latency_ms=latency_ms,
        )
        return True

    async def get_with_health(self, node_id: str) -> tuple[NodeInfo, dict[str, Any]] | None:
        """Get node with current health metadata.

        Args:
            node_id: Unique node identifier.

        Returns:
            Tuple of (NodeInfo, health_dict) if found, None otherwise.
        """
        node = await self.get(node_id)
        if not node:
            return None

        health = await self.get_health(node_id)
        if not health:
            health = {
                "health_status": NodeHealthStatus.UNKNOWN,
                "health_latency_ms": None,
                "health_error": None,
                "health_check_count": 0,
                "consecutive_failures": 0,
                "last_health_check": None,
                "last_health_attempt": None,
            }

        return (node, health)

    async def list_healthy_nodes(self) -> list[NodeInfo]:
        """List nodes that are currently healthy or offline (not explicitly unhealthy).

        Returns:
            List of NodeInfo instances for healthy/offline nodes.
        """
        rows = await self._db.fetchall(
            """SELECT * FROM nodes
               WHERE health_status IN (?, ?)
               ORDER BY created_at DESC""",
            (NodeHealthStatus.HEALTHY.value, NodeHealthStatus.OFFLINE.value),
        )
        return [self._row_to_node(row) for row in rows]

    def _row_to_node(self, row) -> NodeInfo:
        """Convert database row to NodeInfo.

        Args:
            row: Database row from aiosqlite.

        Returns:
            NodeInfo instance.
        """
        return NodeInfo(
            node_id=row["node_id"],
            name=row["name"],
            hostname=row["hostname"],
            status=NodeStatus(row["status"]),
            last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
        )
