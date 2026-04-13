"""Fail-closed policy engine for node access control."""

from dataclasses import dataclass

from src.hub.services.node_health import NodeHealthService
from src.shared.logging import get_logger
from src.shared.models import NodeStatus
from src.shared.repositories.nodes import NodeRepository
from src.shared.schemas import NodeHealthStatus

logger = get_logger(__name__)


@dataclass
class NodeAccessResult:
    """Result of a node access validation check.

    Attributes:
        approved: Whether access is approved.
        node_id: The node identifier that was checked.
        rejection_reason: Reason for rejection if not approved.
        health_status: Current health status if available.
        warning: Optional warning message.
    """

    approved: bool
    node_id: str
    rejection_reason: str | None = None
    health_status: NodeHealthStatus | None = None
    warning: str | None = None


class NodePolicy:
    """Policy engine for node access control - fail closed by default.

    This policy enforces that:
    - Unknown nodes are rejected (not in registry)
    - Unhealthy nodes are rejected
    - Offline nodes are allowed with a warning
    - Unknown health status defaults to rejection (fail closed)
    """

    def __init__(
        self,
        node_repo: NodeRepository,
        health_service: NodeHealthService,
    ):
        """Initialize NodePolicy.

        Args:
            node_repo: NodeRepository for node lookups.
            health_service: NodeHealthService for health status checks.
        """
        self._repo = node_repo
        self._health = health_service

    async def validate_node_access(self, node_id: str) -> NodeAccessResult:
        """Validate access to a node.

        This is the main entry point for node access control.
        Implements fail-closed behavior:
        - Unknown nodes → REJECT
        - Unhealthy nodes → REJECT
        - Offline nodes → APPROVE with warning
        - Unknown health → REJECT

        Args:
            node_id: Node identifier to validate.

        Returns:
            NodeAccessResult with approval status and reason.
        """
        # 1. Check if node exists in registry
        node = await self._repo.get(node_id)
        if not node:
            logger.warning(
                "node_access_rejected_unknown",
                node_id=node_id,
                reason="unknown_node",
            )
            return NodeAccessResult(
                approved=False,
                node_id=node_id,
                rejection_reason="unknown_node",
            )

        # 2. Get health status
        health = await self._health.get_node_health(node_id)

        # 3. Apply fail-closed decision matrix
        if health:
            health_status = health.health_status

            # Unhealthy → REJECT
            if health_status == NodeHealthStatus.UNHEALTHY:
                logger.warning(
                    "node_access_rejected_unhealthy",
                    node_id=node_id,
                    health_status=health_status.value,
                    error=health.health_error,
                )
                return NodeAccessResult(
                    approved=False,
                    node_id=node_id,
                    rejection_reason="node_unhealthy",
                    health_status=health_status,
                )

            # Unknown → REJECT (fail closed)
            if health_status == NodeHealthStatus.UNKNOWN:
                logger.warning(
                    "node_access_rejected_unknown_health",
                    node_id=node_id,
                    health_status=health_status.value,
                )
                return NodeAccessResult(
                    approved=False,
                    node_id=node_id,
                    rejection_reason="unknown_health_status",
                    health_status=health_status,
                )

            # Offline → REJECT (fail closed)
            if health_status == NodeHealthStatus.OFFLINE:
                logger.warning(
                    "node_access_rejected_offline",
                    node_id=node_id,
                    health_status=health_status.value,
                    error=health.health_error,
                )
                return NodeAccessResult(
                    approved=False,
                    node_id=node_id,
                    rejection_reason="node_offline",
                    health_status=health_status,
                )

            # Healthy → APPROVE
            if health_status == NodeHealthStatus.HEALTHY:
                logger.info(
                    "node_access_approved",
                    node_id=node_id,
                    health_status=health_status.value,
                )
                return NodeAccessResult(
                    approved=True,
                    node_id=node_id,
                    health_status=health_status,
                )

        # No health data available → REJECT (fail closed)
        # This ensures we don't allow access to nodes we haven't verified
        logger.warning(
            "node_access_rejected_no_health_data",
            node_id=node_id,
        )
        return NodeAccessResult(
            approved=False,
            node_id=node_id,
            rejection_reason="no_health_data",
        )

    async def validate_node_list_access(self, node_ids: list[str]) -> list[str]:
        """Validate access for multiple nodes.

        Filters the provided list to only include nodes that are approved.

        Args:
            node_ids: List of node identifiers to validate.

        Returns:
            List of approved node identifiers.
        """
        approved = []

        for node_id in node_ids:
            result = await self.validate_node_access(node_id)
            if result.approved:
                approved.append(node_id)

        return approved

    async def get_accessible_nodes(self) -> list[str]:
        """Get list of all accessible node IDs.

        Returns nodes that are registered and not explicitly blocked.
        This is useful for discovering what nodes can be accessed.

        Returns:
            List of accessible node identifiers.
        """
        nodes = await self._repo.list_all()
        accessible = []

        for node in nodes:
            result = await self.validate_node_access(node.node_id)
            if result.approved:
                accessible.append(node.node_id)

        return accessible

    async def check_node_reachable(self, node_id: str) -> bool:
        """Quick check if a node is reachable.

        A lighter-weight check that just verifies the node exists
        and has recent health data indicating it's online/healthy.

        Args:
            node_id: Node identifier to check.

        Returns:
            True if node appears reachable, False otherwise.
        """
        node = await self._repo.get(node_id)
        if not node:
            return False

        health = await self._health.get_node_health(node_id)

        # If we have health data and it's not unhealthy, consider it reachable
        if health and health.health_status != NodeHealthStatus.UNHEALTHY:
            return True

        # If no health data, check node status directly
        if node.status in (NodeStatus.HEALTHY, NodeStatus.OFFLINE):
            return True

        return False
