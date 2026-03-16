"""LLM service policy with fail-closed validation."""

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, LLMServiceType
from src.shared.repositories.llm_services import LLMServiceRepository

logger = get_logger(__name__)


class LLMServicePolicy:
    """Policy engine for LLM service access control.

    This policy enforces fail-closed behavior: unknown or invalid LLM services
    are rejected by raising ValueError.
    """

    def __init__(self, llm_repo: LLMServiceRepository):
        """Initialize with LLM service repository.

        Args:
            llm_repo: Repository for LLM service CRUD operations.
        """
        self._repo = llm_repo

    async def validate_service_access(self, service_id: str) -> LLMServiceInfo:
        """Validate access to an LLM service.

        Args:
            service_id: Service identifier to validate.

        Returns:
            LLMServiceInfo if service exists and is accessible.

        Raises:
            ValueError: If service is unknown or inaccessible.
        """
        service = await self._repo.get(service_id)
        if not service:
            logger.warning(
                "llm_service_access_denied",
                service_id=service_id,
                reason="unknown_service",
            )
            raise ValueError(f"Unknown LLM service: {service_id}")

        logger.info("llm_service_access_granted", service_id=service_id)
        return service

    async def validate_service_by_name(self, name: str) -> LLMServiceInfo:
        """Validate access to an LLM service by name.

        Args:
            name: Service name to validate.

        Returns:
            LLMServiceInfo if service exists and is accessible.

        Raises:
            ValueError: If service is unknown or inaccessible.
        """
        service = await self._repo.get_by_name(name)
        if not service:
            logger.warning(
                "llm_service_access_denied",
                name=name,
                reason="unknown_service_name",
            )
            raise ValueError(f"Unknown LLM service name: {name}")

        logger.info("llm_service_access_granted", name=name)
        return service

    async def list_services(self) -> list[LLMServiceInfo]:
        """List all registered LLM services.

        Returns:
            List of all LLMServiceInfo instances.
        """
        return await self._repo.list_all()

    async def list_services_by_type(self, service_type: LLMServiceType) -> list[LLMServiceInfo]:
        """List LLM services of a specific type.

        Args:
            service_type: Type of service to filter by.

        Returns:
            List of LLMServiceInfo instances of the specified type.
        """
        return await self._repo.list_by_type(service_type)

    async def get_coding_agent_service(self) -> LLMServiceInfo | None:
        """Get the configured coding agent (OpenCode) service.

        Returns:
            LLMServiceInfo for OpenCode service, or None if not configured.
        """
        services = await self._repo.list_by_type(LLMServiceType.OPENCODE)
        return services[0] if services else None

    async def get_embedding_service(self) -> LLMServiceInfo | None:
        """Get the configured embedding service.

        Returns:
            LLMServiceInfo for embedding service, or None if not configured.
        """
        services = await self._repo.list_by_type(LLMServiceType.EMBEDDING)
        return services[0] if services else None
