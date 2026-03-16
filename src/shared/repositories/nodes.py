"""Node repository for CRUD operations on the nodes table."""

import json
from datetime import datetime
from typing import Any

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import NodeInfo, NodeStatus

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
