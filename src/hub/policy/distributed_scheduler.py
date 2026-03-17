"""Distributed scheduler for node-aware LLM service selection.

This module provides the DistributedScheduler class that extends TaskRoutingPolicy
with node-level awareness, considering health, latency, and node capabilities
during service selection.
"""

from typing import TYPE_CHECKING

from src.hub.services.node_health import NodeHealth, NodeHealthService
from src.hub.services.node_health import NodeHealthStatus as HealthStatus
from src.shared.logging import get_logger
from src.shared.models import (
    LLMServiceInfo,
    LLMServiceType,
    NodeHealthInfo,
    NodeInfo,
    NodeStatus,
    SchedulerInput,
    SchedulerResult,
    ServiceNodePair,
    TaskClass,
)
from src.shared.repositories.llm_services import LLMServiceRepository
from src.shared.repositories.nodes import NodeRepository

# Type hints for forward references
if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.hub.policy.task_routing_policy import TaskRoutingPolicy

logger = get_logger(__name__)

# Default fallback chain order when no health data available
DEFAULT_FALLBACK_ORDER: list[LLMServiceType] = [
    LLMServiceType.OPENCODE,
    LLMServiceType.LLAMA,
    LLMServiceType.HELPER,
    LLMServiceType.EMBEDDING,
]


class DistributedScheduler:
    """Distributed scheduler with node-aware service selection.

    This scheduler extends TaskRoutingPolicy with node-level awareness,
    considering health, latency, and node capabilities during selection.
    It provides:
    - Health-aware filtering (excludes unhealthy nodes)
    - Latency-aware selection (prefers lower latency)
    - Bounded fallback chain with explicit retry limits
    - Node preference support (preferred_node_id)
    """

    def __init__(
        self,
        task_routing_policy: "TaskRoutingPolicy",
        node_health_service: NodeHealthService,
        node_repository: NodeRepository,
        llm_service_policy: "LLMServicePolicy",
        llm_service_repo: LLMServiceRepository,
    ):
        """Initialize the distributed scheduler.

        Args:
            task_routing_policy: Task-based routing from SCHED-001.
            node_health_service: Health polling service from CORE-004.
            node_repository: Node registry access.
            llm_service_policy: Service validation and listing.
            llm_service_repo: LLM service repository for direct access.
        """
        self._task_routing = task_routing_policy
        self._health_service = node_health_service
        self._node_repo = node_repository
        self._llm_policy = llm_service_policy
        self._llm_repo = llm_service_repo

    async def schedule(self, input: SchedulerInput) -> SchedulerResult:
        """Make a scheduling decision based on inputs.

        Args:
            input: All scheduling inputs.

        Returns:
            Scheduling result with selected service/node.

        Raises:
            ValueError: If no suitable service/node found.
        """
        logger.info(
            "distributed_scheduler_start",
            task_class=input.task_class.value,
            preferred_node=input.preferred_node_id,
            preferred_service=input.preferred_service_id,
            trace_id=input.trace_id,
        )

        # Step 1: Get candidate services from task routing
        candidates = await self._get_candidates(input)

        if not candidates:
            logger.warning(
                "distributed_scheduler_no_candidates",
                task_class=input.task_class.value,
                trace_id=input.trace_id,
            )
            raise ValueError(
                f"No available LLM services found for task class: {input.task_class.value}"
            )

        # Step 2: Enrich candidates with node information
        enriched = await self._enrich_with_node_info(candidates, input)

        # Step 3: Filter by health and constraints
        filtered = self._filter_by_health(enriched, input)

        if not filtered:
            logger.warning(
                "distributed_scheduler_no_healthy_candidates",
                task_class=input.task_class.value,
                trace_id=input.trace_id,
            )
            # If no healthy candidates, fall back to all candidates
            # This allows routing to attempt even if health is unknown
            filtered = enriched

        # Step 4: Select best candidate
        selected = self._select_best(filtered, input)

        # Step 5: Build fallback chain
        fallback_chain = self._build_fallback_chain(filtered, selected, input)

        # Step 6: Build result
        result = SchedulerResult(
            selected_service=selected.service,
            selected_node=selected.node,
            node_health=selected.health,
            fallback_chain=fallback_chain,
            selection_reason=selected.reason,
            latency_ms=selected.health.latency_ms if selected.health else None,
        )

        logger.info(
            "distributed_scheduler_selected",
            service_id=selected.service.service_id,
            node_id=selected.node.node_id,
            latency_ms=result.latency_ms,
            fallback_count=len(fallback_chain),
            trace_id=input.trace_id,
        )

        return result

    async def _get_candidates(
        self,
        input: SchedulerInput,
    ) -> list[LLMServiceInfo]:
        """Get candidate services based on scheduling input.

        Args:
            input: Scheduler input.

        Returns:
            List of candidate LLMServiceInfo.
        """
        # If explicit service specified, validate and use it
        if input.preferred_service_id:
            try:
                service = await self._llm_policy.validate_service_access(input.preferred_service_id)
                return [service]
            except ValueError as e:
                logger.warning(
                    "distributed_scheduler_preferred_service_invalid",
                    service_id=input.preferred_service_id,
                    error=str(e),
                )
                # Fall through to task routing

        # If explicit service type specified, filter by type
        if input.preferred_service_type:
            services = await self._llm_policy.list_services_by_type(input.preferred_service_type)
            if services:
                return services

        # Use task routing policy to get fallback chain
        return await self._task_routing.get_fallback_chain()

    async def _enrich_with_node_info(
        self,
        services: list[LLMServiceInfo],
        input: SchedulerInput,
    ) -> list[ServiceNodePair]:
        """Enrich services with node information.

        Services are associated with nodes via metadata stored in the service.
        The node_id is extracted from service metadata or inferred from the
        endpoint hostname.

        Args:
            services: List of candidate services.
            input: Scheduler input.

        Returns:
            List of ServiceNodePair with node information.
        """
        # Get all nodes
        all_nodes = await self._node_repo.list_all()
        nodes_by_id = {node.node_id: node for node in all_nodes}

        enriched: list[ServiceNodePair] = []

        for service in services:
            # Try to get node_id from service metadata
            # In practice, this would come from the service repository metadata
            node_id = await self._get_node_for_service(service)

            if node_id and node_id in nodes_by_id:
                node = nodes_by_id[node_id]
                health = await self._get_node_health(node)
                enriched.append(
                    ServiceNodePair(
                        service=service,
                        node=node,
                        health=health,
                        reason=f"Service {service.service_id} on node {node_id}",
                    )
                )
            elif input.preferred_node_id is None:
                # Only add to candidates without node if no node preference specified
                # This allows services without explicit node association
                enriched.append(
                    ServiceNodePair(
                        service=service,
                        node=NodeInfo(
                            node_id="unknown",
                            name="Unknown Node",
                            hostname="unknown",
                            status=NodeStatus.UNKNOWN,
                        ),
                        health=None,
                        reason=f"Service {service.service_id} has no node association",
                    )
                )

        return enriched

    async def _get_node_for_service(self, service: LLMServiceInfo) -> str | None:
        """Get the node ID associated with a service.

        This method looks up the node_id from the service repository metadata.
        In the current implementation, services don't have explicit node_id fields,
        so this returns None and services are treated as node-agnostic.

        Args:
            service: LLM service to look up.

        Returns:
            Node ID if found, None otherwise.
        """
        # In a more complete implementation, this would query the service metadata
        # or a separate service-to-node mapping table
        # For now, we return None to indicate node-agnostic services
        return None

    async def _get_node_health(self, node: NodeInfo) -> NodeHealthInfo:
        """Get health information for a node.

        Args:
            node: Node to check health for.

        Returns:
            NodeHealthInfo with health status.
        """
        health: NodeHealth | None = None
        try:
            health = await self._health_service.get_node_health(node.node_id)
        except Exception as e:
            logger.warning(
                "distributed_scheduler_health_check_failed",
                node_id=node.node_id,
                error=str(e),
            )

        if health is None:
            return NodeHealthInfo(
                node_id=node.node_id,
                health_status=NodeStatus.UNKNOWN,
                is_healthy=False,  # Fail closed - unknown means not healthy
                latency_ms=None,
                is_stale=True,
            )

        # Determine if node is healthy enough for routing
        is_healthy = health.health_status == HealthStatus.HEALTHY or (
            health.health_status == HealthStatus.UNKNOWN and not health.is_stale
        )

        return NodeHealthInfo(
            node_id=node.node_id,
            health_status=NodeStatus(health.health_status.value),
            is_healthy=is_healthy,
            latency_ms=health.health_latency_ms,
            is_stale=health.is_stale,
        )

    def _filter_by_health(
        self,
        candidates: list[ServiceNodePair],
        input: SchedulerInput,
    ) -> list[ServiceNodePair]:
        """Filter candidates by health status and constraints.

        Args:
            candidates: List of service-node pairs.
            input: Scheduler input with constraints.

        Returns:
            Filtered list of candidates.
        """
        filtered: list[ServiceNodePair] = []

        for candidate in candidates:
            # Skip excluded nodes
            if input.exclude_node_ids and candidate.node.node_id in input.exclude_node_ids:
                logger.debug(
                    "distributed_scheduler_node_excluded",
                    node_id=candidate.node.node_id,
                    trace_id=input.trace_id,
                )
                continue

            # Check if node meets health requirements
            if candidate.health:
                # Skip unhealthy nodes
                if (
                    not candidate.health.is_healthy
                    and candidate.health.health_status != NodeStatus.UNKNOWN
                ):
                    logger.debug(
                        "distributed_scheduler_node_unhealthy",
                        node_id=candidate.node.node_id,
                        health_status=candidate.health.health_status.value,
                        trace_id=input.trace_id,
                    )
                    continue

                # Check latency constraint
                if (
                    input.max_latency_ms is not None
                    and candidate.health.latency_ms is not None
                    and candidate.health.latency_ms > input.max_latency_ms
                ):
                    logger.debug(
                        "distributed_scheduler_node_latency_exceeded",
                        node_id=candidate.node.node_id,
                        latency_ms=candidate.health.latency_ms,
                        max_latency_ms=input.max_latency_ms,
                        trace_id=input.trace_id,
                    )
                    continue

            filtered.append(candidate)

        return filtered

    def _select_best(
        self,
        candidates: list[ServiceNodePair],
        input: SchedulerInput,
    ) -> ServiceNodePair:
        """Select best candidate from filtered list.

        Selection priority:
        1. Preferred node (if specified)
        2. Lowest latency
        3. Healthiest node (healthy > unknown > unhealthy)
        4. First in list

        Args:
            candidates: Filtered list of candidates.
            input: Scheduler input.

        Returns:
            Best ServiceNodePair.

        Raises:
            ValueError: If no candidates available.
        """
        if not candidates:
            raise ValueError("No candidates available for selection")

        # If preferred node specified, try to use it
        if input.preferred_node_id:
            for candidate in candidates:
                if candidate.node.node_id == input.preferred_node_id:
                    return candidate

        # Sort by latency (lowest first), then by health status
        def sort_key(c: ServiceNodePair) -> tuple:
            latency = c.health.latency_ms if c.health else float("inf")
            # Health priority: healthy = 0, unknown = 1, unhealthy = 2
            health_priority = (
                0
                if (c.health and c.health.is_healthy)
                else (1 if (c.health and c.health.health_status == NodeStatus.UNKNOWN) else 2)
            )
            return (health_priority, latency)

        sorted_candidates = sorted(candidates, key=sort_key)

        selected = sorted_candidates[0]

        # Build selection reason
        reason_parts = []
        if input.preferred_node_id and selected.node.node_id == input.preferred_node_id:
            reason_parts.append("preferred node")
        if selected.health and selected.health.latency_ms:
            reason_parts.append(f"latency {selected.health.latency_ms}ms")
        if selected.health and selected.health.is_healthy:
            reason_parts.append("healthy")
        if not reason_parts:
            reason_parts.append("first available")

        selected.reason = ", ".join(reason_parts)

        return selected

    def _build_fallback_chain(
        self,
        candidates: list[ServiceNodePair],
        selected: ServiceNodePair,
        input: SchedulerInput,
    ) -> list[SchedulerResult]:
        """Build ordered fallback chain.

        Args:
            candidates: All candidates (filtered).
            selected: Selected candidate.
            input: Scheduler input.

        Returns:
            Ordered list of fallback options.
        """
        fallback_chain: list[SchedulerResult] = []
        max_fallbacks = min(input.max_fallback_attempts, len(candidates) - 1)

        # Build fallback chain from remaining candidates
        for i, candidate in enumerate(candidates[: max_fallbacks + 1]):
            if candidate.service.service_id == selected.service.service_id:
                continue

            fallback_chain.append(
                SchedulerResult(
                    selected_service=candidate.service,
                    selected_node=candidate.node,
                    node_health=candidate.health,
                    fallback_chain=[],
                    selection_reason=candidate.reason or f"fallback position {i}",
                    latency_ms=candidate.health.latency_ms if candidate.health else None,
                )
            )

        return fallback_chain


class DistributedSchedulerError(Exception):
    """Error raised when distributed scheduling fails."""

    def __init__(
        self,
        message: str,
        task_class: TaskClass,
        attempted_services: list[str],
        attempted_nodes: list[str],
        errors: list[str],
    ):
        """Initialize the scheduling error.

        Args:
            message: Error message.
            task_class: The task class that was being scheduled.
            attempted_services: List of service IDs attempted.
            attempted_nodes: List of node IDs attempted.
            errors: List of error messages from each attempt.
        """
        super().__init__(message)
        self.task_class = task_class
        self.attempted_services = attempted_services
        self.attempted_nodes = attempted_nodes
        self.errors = errors
