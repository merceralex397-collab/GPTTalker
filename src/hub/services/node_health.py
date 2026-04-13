"""Health polling service for node agents."""

from datetime import UTC, datetime
from typing import Any

import httpx

from src.hub.services.auth import NodeAuthHandler
from src.shared.logging import get_logger
from src.shared.models import NodeInfo
from src.shared.repositories.nodes import NodeRepository
from src.shared.schemas import NodeHealthStatus

logger = get_logger(__name__)


class NodeHealth:
    """Explicit health metadata for a node.

    This class represents the computed health state of a node based on
    periodic health checks.
    """

    # Thresholds for health computation
    STALE_THRESHOLD_SECONDS = 300  # 5 minutes
    MAX_CONSECUTIVE_FAILURES = 3
    HEALTHY_LATENCY_THRESHOLD_MS = 5000  # 5 seconds

    def __init__(
        self,
        node_id: str,
        health_status: NodeHealthStatus = NodeHealthStatus.UNKNOWN,
        last_health_check: datetime | None = None,
        last_health_attempt: datetime | None = None,
        health_latency_ms: int | None = None,
        health_error: str | None = None,
        health_check_count: int = 0,
        consecutive_failures: int = 0,
    ):
        """Initialize NodeHealth.

        Args:
            node_id: Node identifier
            health_status: Current health status
            last_health_check: Last successful health check time
            last_health_attempt: Last health check attempt (successful or not)
            health_latency_ms: Last health check latency
            health_error: Last health check error message
            health_check_count: Total number of health checks performed
            consecutive_failures: Number of consecutive health check failures
        """
        self.node_id = node_id
        self.health_status = health_status
        self.last_health_check = last_health_check
        self.last_health_attempt = last_health_attempt
        self.health_latency_ms = health_latency_ms
        self.health_error = health_error
        self.health_check_count = health_check_count
        self.consecutive_failures = consecutive_failures

    @property
    def is_stale(self) -> bool:
        """Check if node health data is stale.

        A node is considered stale if no successful health check
        has been performed within the threshold period.

        Returns:
            True if health data is stale, False otherwise.
        """
        if not self.last_health_check:
            return True
        elapsed = (datetime.now(UTC) - self.last_health_check).total_seconds()
        return elapsed > self.STALE_THRESHOLD_SECONDS

    @property
    def should_retry(self) -> bool:
        """Check if health check should be retried.

        Returns:
            True if the node should be retried (under failure limit).
        """
        return self.consecutive_failures < self.MAX_CONSECUTIVE_FAILURES

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of health data.
        """
        return {
            "node_id": self.node_id,
            "health_status": self.health_status.value,
            "last_health_check": self.last_health_check.isoformat()
            if self.last_health_check
            else None,
            "last_health_attempt": self.last_health_attempt.isoformat()
            if self.last_health_attempt
            else None,
            "health_latency_ms": self.health_latency_ms,
            "health_error": self.health_error,
            "health_check_count": self.health_check_count,
            "consecutive_failures": self.consecutive_failures,
            "is_stale": self.is_stale,
            "should_retry": self.should_retry,
        }


class NodeHealthService:
    """Service for polling and tracking node health.

    This service performs periodic health checks on registered nodes
    and maintains health metadata for fail-closed policy decisions.
    """

    HEALTH_ENDPOINT = "/health"
    DEFAULT_TIMEOUT = 10  # seconds
    HEALTHY_LATENCY_THRESHOLD_MS = NodeHealth.HEALTHY_LATENCY_THRESHOLD_MS

    def __init__(
        self,
        node_repo: NodeRepository,
        http_client: httpx.AsyncClient,
        auth_handler: NodeAuthHandler | None = None,
    ):
        """Initialize NodeHealthService.

        Args:
            node_repo: NodeRepository for node operations.
            http_client: Async HTTP client for health check requests.
            auth_handler: Optional authentication handler for node requests.
        """
        self._repo = node_repo
        self._client = http_client
        self._auth = auth_handler

    async def check_node_health(self, node: NodeInfo) -> NodeHealth:
        """Perform health check on a single node.

        Makes an HTTP GET request to the node's health endpoint and
        computes the health status based on the response.

        Args:
            node: NodeInfo instance to check.

        Returns:
            NodeHealth instance with computed health status.
        """
        health = NodeHealth(node_id=node.node_id)
        health.last_health_attempt = datetime.now(UTC)

        try:
            url = f"http://{node.hostname}{self.HEALTH_ENDPOINT}"

            # Build request headers (including auth if available)
            headers = {}
            if self._auth:
                headers = self._auth.get_headers()

            response = await self._client.get(
                url,
                timeout=httpx.Timeout(self.DEFAULT_TIMEOUT),
                headers=headers,
            )
            latency_ms = int(response.elapsed.total_seconds() * 1000)

            health.health_check_count += 1
            health.health_latency_ms = latency_ms

            if response.status_code == 200:
                # Successful health check
                health.health_status = self._compute_health_status(
                    latency_ms=latency_ms,
                    error=None,
                )
                health.last_health_check = datetime.now(UTC)
                health.health_error = None
                health.consecutive_failures = 0

                logger.info(
                    "node_health_check_success",
                    node_id=node.node_id,
                    latency_ms=latency_ms,
                )
            else:
                # Non-200 response
                health.health_status = NodeHealthStatus.UNHEALTHY
                health.health_error = f"HTTP {response.status_code}"
                health.consecutive_failures += 1

                logger.warning(
                    "node_health_check_error",
                    node_id=node.node_id,
                    status_code=response.status_code,
                )

        except httpx.TimeoutException:
            health.health_check_count += 1
            health.health_status = NodeHealthStatus.UNHEALTHY
            health.health_error = "timeout"
            health.consecutive_failures += 1
            health.health_latency_ms = self.DEFAULT_TIMEOUT * 1000

            logger.warning(
                "node_health_check_timeout",
                node_id=node.node_id,
                timeout_seconds=self.DEFAULT_TIMEOUT,
            )

        except httpx.ConnectError as e:
            health.health_check_count += 1
            health.health_status = NodeHealthStatus.OFFLINE
            health.health_error = f"connection_error: {str(e)}"
            health.consecutive_failures += 1

            logger.warning(
                "node_health_check_offline",
                node_id=node.node_id,
                error=str(e),
            )

        except Exception as e:
            health.health_check_count += 1
            health.health_status = NodeHealthStatus.UNHEALTHY
            health.health_error = f"unexpected_error: {str(e)}"
            health.consecutive_failures += 1

            logger.error(
                "node_health_check_exception",
                node_id=node.node_id,
                error=str(e),
            )

        # Persist health update
        await self._repo.update_health(
            node_id=node.node_id,
            status=health.health_status,
            latency_ms=health.health_latency_ms,
            error=health.health_error,
            check_count=health.health_check_count,
            consecutive_failures=health.consecutive_failures,
            last_check=health.last_health_check,
            last_attempt=health.last_health_attempt,
        )

        return health

    async def check_all_nodes(self) -> list[NodeHealth]:
        """Check health of all registered nodes.

        Returns:
            List of NodeHealth instances for all registered nodes.
        """
        nodes = await self._repo.list_all()
        results = []

        for node in nodes:
            health = await self.check_node_health(node)
            results.append(health)

        return results

    async def get_node_health(self, node_id: str) -> NodeHealth | None:
        """Get current health metadata for a node.

        Args:
            node_id: Node identifier.

        Returns:
            NodeHealth instance if node exists, None otherwise.
        """
        health_data = await self._repo.get_health(node_id)
        if not health_data:
            return None

        return NodeHealth(
            node_id=node_id,
            health_status=health_data.get("health_status", NodeHealthStatus.UNKNOWN),
            last_health_check=health_data.get("last_health_check"),
            last_health_attempt=health_data.get("last_health_attempt"),
            health_latency_ms=health_data.get("health_latency_ms"),
            health_error=health_data.get("health_error"),
            health_check_count=health_data.get("health_check_count", 0),
            consecutive_failures=health_data.get("consecutive_failures", 0),
        )

    def _compute_health_status(
        self,
        latency_ms: int | None,
        error: str | None,
    ) -> NodeHealthStatus:
        """Compute health status based on response metrics.

        Args:
            latency_ms: Response latency in milliseconds.
            error: Error message if any.

        Returns:
            NodeHealthStatus computed from metrics.
        """
        if error:
            return NodeHealthStatus.UNHEALTHY

        if latency_ms is not None and latency_ms > self.HEALTHY_LATENCY_THRESHOLD_MS:
            return NodeHealthStatus.UNHEALTHY

        return NodeHealthStatus.HEALTHY
