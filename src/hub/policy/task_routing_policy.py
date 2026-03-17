"""Task routing policy for LLM service selection.

This module provides the routing policy that determines which LLM service
to use based on task classification and service capabilities.
"""

from typing import TYPE_CHECKING

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, LLMServiceType, TaskClass

# Type hints for forward references
if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy

logger = get_logger(__name__)

# Default mapping from task class to preferred service types
# This mapping is used when service capabilities are not available
TASK_CLASS_MAPPING: dict[TaskClass, list[LLMServiceType]] = {
    TaskClass.CODING: [LLMServiceType.OPENCODE, LLMServiceType.LLAMA],
    TaskClass.CHAT: [LLMServiceType.LLAMA, LLMServiceType.HELPER],
    TaskClass.EMBEDDING: [LLMServiceType.EMBEDDING],
    TaskClass.SUMMARIZATION: [LLMServiceType.LLAMA, LLMServiceType.HELPER],
    TaskClass.REASONING: [LLMServiceType.LLAMA],
    TaskClass.SEARCH: [LLMServiceType.EMBEDDING],  # For query embedding
}


class TaskRoutingPolicy:
    """Policy engine for task-based LLM service routing.

    This policy selects the appropriate LLM service based on task classification,
    service capabilities, and fallback behavior.
    """

    def __init__(
        self,
        llm_service_policy: "LLMServicePolicy",
        task_class: TaskClass,
        preferred_service_id: str | None = None,
    ):
        """Initialize the task routing policy.

        Args:
            llm_service_policy: Policy for validating and listing services.
            task_class: The task classification for routing.
            preferred_service_id: Optional specific service to prefer.
        """
        self._llm_policy = llm_service_policy
        self._task_class = task_class
        self._preferred_service_id = preferred_service_id

    async def select_service(self) -> LLMServiceInfo | None:
        """Select the best service for the task class.

        Returns:
            Selected LLMServiceInfo, or None if no suitable service found.

        Raises:
            ValueError: If preferred service is invalid.
        """
        # If preferred service specified, validate and use it
        if self._preferred_service_id:
            try:
                service = await self._llm_policy.validate_service_access(self._preferred_service_id)
                logger.info(
                    "task_routing_preferred_service_selected",
                    service_id=service.service_id,
                    service_type=service.type.value,
                    task_class=self._task_class.value,
                )
                return service
            except ValueError as e:
                logger.warning(
                    "task_routing_preferred_service_invalid",
                    service_id=self._preferred_service_id,
                    error=str(e),
                )
                raise

        # Get fallback chain and return first available
        fallback_chain = await self.get_fallback_chain()
        if fallback_chain:
            primary = fallback_chain[0]
            logger.info(
                "task_routing_service_selected",
                service_id=primary.service_id,
                service_type=primary.type.value,
                task_class=self._task_class.value,
                fallback_count=len(fallback_chain) - 1,
            )
            return primary

        logger.warning(
            "task_routing_no_service_available",
            task_class=self._task_class.value,
        )
        return None

    async def get_fallback_chain(
        self,
    ) -> list[LLMServiceInfo]:
        """Get ordered fallback services for the task class.

        Returns:
            Ordered list of LLMServiceInfo, best first.
        """
        # Get preferred service types for this task class
        preferred_types = TASK_CLASS_MAPPING.get(self._task_class, [LLMServiceType.LLAMA])

        # Collect services of each type until we have candidates
        candidates: list[LLMServiceInfo] = []

        for service_type in preferred_types:
            services = await self._llm_policy.list_services_by_type(service_type)
            for service in services:
                # Skip if already in candidates
                if service.service_id not in [s.service_id for s in candidates]:
                    candidates.append(service)

        # Add any remaining services not yet included
        all_services = await self._llm_policy.list_services()
        for service in all_services:
            if service.service_id not in [s.service_id for s in candidates]:
                candidates.append(service)

        logger.debug(
            "task_routing_fallback_chain_built",
            task_class=self._task_class.value,
            chain_length=len(candidates),
            service_ids=[s.service_id for s in candidates],
        )
        return candidates

    def should_fallback(self, error: Exception) -> bool:
        """Determine if an error warrants fallback to next service.

        Args:
            error: The error that occurred.

        Returns:
            True if fallback should be attempted.
        """
        error_msg = str(error).lower()

        # Do NOT fallback on auth failures - these are config errors
        auth_failure_indicators = [
            "unauthorized",
            "authentication",
            "api key",
            "forbidden",
            "403",
        ]
        for indicator in auth_failure_indicators:
            if indicator in error_msg:
                logger.info(
                    "task_routing_no_fallback_auth_failure",
                    error=str(error),
                )
                return False

        # Fallback on availability issues
        fallback_indicators = [
            "not found",
            "404",
            "unavailable",
            "503",
            "timeout",
            "connection",
            "refused",
            "reset",
        ]
        for indicator in fallback_indicators:
            if indicator in error_msg:
                logger.info(
                    "task_routing_fallback_for_error",
                    error=str(error),
                    error_type=type(error).__name__,
                )
                return True

        # Default: don't fallback on unknown errors
        logger.warning(
            "task_routing_no_fallback_unknown_error",
            error=str(error),
            error_type=type(error).__name__,
        )
        return False


class TaskRoutingError(Exception):
    """Error raised when task routing fails."""

    def __init__(
        self,
        message: str,
        task_class: TaskClass,
        attempted_services: list[str],
        errors: list[str],
    ):
        """Initialize the routing error.

        Args:
            message: Error message.
            task_class: The task class that was being routed.
            attempted_services: List of service IDs attempted.
            errors: List of error messages from each attempt.
        """
        super().__init__(message)
        self.task_class = task_class
        self.attempted_services = attempted_services
        self.errors = errors
