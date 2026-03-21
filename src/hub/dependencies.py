"""Dependency injection providers for the GPTTalker hub."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import aiosqlite
import httpx
from fastapi import Depends, Request

from src.hub.config import HubConfig, get_hub_config
from src.hub.policy.engine import PolicyEngine
from src.hub.policy.llm_service_policy import LLMServicePolicy
from src.hub.policy.node_policy import NodePolicy
from src.hub.policy.repo_policy import RepoPolicy
from src.hub.policy.task_routing_policy import TaskRoutingPolicy
from src.hub.policy.write_target_policy import WriteTargetPolicy
from src.hub.services.auth import NodeAuthHandler
from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.indexing_pipeline import IndexingPipeline
from src.hub.services.llm_client import LLMServiceClient
from src.hub.services.node_client import HubNodeClient
from src.hub.services.node_health import NodeHealthService
from src.hub.services.opencode_adapter import OpenCodeAdapter
from src.hub.services.qdrant_client import (
    QdrantClientWrapper,
)
from src.hub.services.qdrant_client import (
    get_qdrant_client as get_qdrant,
)
from src.hub.services.session_store import SessionStore
from src.hub.tool_router import ToolRegistry
from src.hub.tool_routing import PolicyAwareToolRouter
from src.shared.database import DatabaseManager
from src.shared.logging import get_logger
from src.shared.models import TaskClass
from src.shared.repositories.audit_log import AuditLogRepository
from src.shared.repositories.generated_docs import GeneratedDocsRepository
from src.shared.repositories.issues import IssueRepository
from src.shared.repositories.llm_services import LLMServiceRepository
from src.shared.repositories.nodes import NodeRepository
from src.shared.repositories.relationships import RelationshipRepository, RepoOwnerRepository
from src.shared.repositories.repos import RepoRepository
from src.shared.repositories.tasks import TaskRepository
from src.shared.repositories.write_targets import WriteTargetRepository

if TYPE_CHECKING:
    from src.hub.services.aggregation_service import AggregationService
    from src.hub.services.architecture_service import ArchitectureService
    from src.hub.services.bundle_service import BundleService
    from src.hub.services.cross_repo_service import CrossRepoService
    from src.hub.services.indexing_pipeline import IndexingPipeline
    from src.hub.services.relationship_service import RelationshipService

# Logger instance for this module
logger = get_logger(__name__)


async def get_db(request: Request) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get database connection from app state.

    This dependency provides a database connection that is scoped to the
    current request. The connection is retrieved from app state where
    it is stored by the lifespan handler.

    Args:
        request: The current FastAPI request.

    Yields:
        An aiosqlite connection for database operations.

    Raises:
        RuntimeError: If database is not initialized.
    """
    # Get database from app state (set by lifespan)
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")

    yield db_manager.connection


async def get_db_manager_dep(request: Request) -> DatabaseManager:
    """Get the database manager instance.

    Args:
        request: The current FastAPI request.

    Returns:
        The DatabaseManager instance from app state.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return db_manager


def get_config() -> HubConfig:
    """Get hub configuration.

    Returns:
        HubConfig instance with environment overrides.
    """
    return get_hub_config()


def get_hub_logger() -> Any:
    """Get a logger for hub operations.

    Returns:
        Logger instance for hub-specific logging.
    """
    return get_logger("gpttalker-hub")


async def check_database_health(request: Request) -> dict[str, Any]:
    """Check database connectivity.

    This is a dependency that can be used to verify database
    connectivity for health checks.

    Args:
        request: The current FastAPI request.

    Returns:
        Dict with database health status.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        return {"status": "uninitialized", "connected": False}

    try:
        # Try a simple query to verify connectivity
        await db_manager.connection.execute("SELECT 1")
        return {"status": "healthy", "connected": True}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"status": "unhealthy", "connected": False, "error": str(e)}


async def get_node_repository(request: Request) -> NodeRepository:
    """Get node repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        NodeRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return NodeRepository(db_manager)


async def get_node_health_service(
    request: Request,
    node_repo: NodeRepository = Depends(get_node_repository),  # noqa: B008
) -> NodeHealthService:
    """Get node health service from app state or create new instance.

    Args:
        request: The current FastAPI request.
        node_repo: NodeRepository instance.

    Returns:
        NodeHealthService instance.
    """
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Ensure lifespan has run.")
    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")

    auth_handler = NodeAuthHandler(config.node_client_api_key)
    return NodeHealthService(
        node_repo=node_repo,
        http_client=http_client,
        auth_handler=auth_handler,
    )


def get_node_auth_handler(request: Request) -> NodeAuthHandler:
    """Get node authentication handler from config.

    Args:
        request: The current FastAPI request.

    Returns:
        NodeAuthHandler instance.
    """
    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")
    return NodeAuthHandler(config.node_client_api_key)


async def get_node_client(
    request: Request,
    auth_handler: NodeAuthHandler = Depends(get_node_auth_handler),  # noqa: B008
) -> HubNodeClient:
    """Get hub-to-node HTTP client.

    Args:
        request: The current FastAPI request.
        auth_handler: Node authentication handler.

    Returns:
        HubNodeClient instance.
    """
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Ensure lifespan has run.")

    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")

    return HubNodeClient(
        http_client=http_client,
        auth_handler=auth_handler,
        default_timeout=config.node_client_timeout,
        connect_timeout=config.node_client_connect_timeout,
    )


async def get_node_policy(
    node_repo: NodeRepository = Depends(get_node_repository),  # noqa: B008
    health_service: NodeHealthService = Depends(get_node_health_service),  # noqa: B008
) -> NodePolicy:
    """Get node policy engine.

    Args:
        node_repo: NodeRepository instance.
        health_service: NodeHealthService instance.

    Returns:
        NodePolicy instance.
    """
    return NodePolicy(node_repo, health_service)


async def get_repo_repository(request: Request) -> RepoRepository:
    """Get repo repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        RepoRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return RepoRepository(db_manager)


async def get_write_target_repository(request: Request) -> WriteTargetRepository:
    """Get write target repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        WriteTargetRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return WriteTargetRepository(db_manager)


async def get_llm_service_repository(request: Request) -> LLMServiceRepository:
    """Get LLM service repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        LLMServiceRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return LLMServiceRepository(db_manager)


async def get_issue_repository(request: Request) -> IssueRepository:
    """Get issue repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        IssueRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return IssueRepository(db_manager)


async def get_relationship_repository(request: Request) -> RelationshipRepository:
    """Get relationship repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        RelationshipRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return RelationshipRepository(db_manager)


async def get_owner_repository(request: Request) -> RepoOwnerRepository:
    """Get repo owner repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        RepoOwnerRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return RepoOwnerRepository(db_manager)


async def get_generated_docs_repository(request: Request) -> GeneratedDocsRepository:
    """Get generated docs repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        GeneratedDocsRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return GeneratedDocsRepository(db_manager)


async def get_audit_log_repository(request: Request) -> AuditLogRepository:
    """Get audit log repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        AuditLogRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return AuditLogRepository(db_manager)


async def get_task_repository(request: Request) -> TaskRepository:
    """Get task repository from app state.

    Args:
        request: The current FastAPI request.

    Returns:
        TaskRepository instance.
    """
    db_manager: DatabaseManager | None = request.app.state.db_manager
    if db_manager is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return TaskRepository(db_manager)


async def get_repo_policy(
    repo_repo: RepoRepository = Depends(get_repo_repository),  # noqa: B008
) -> RepoPolicy:
    """Get repo policy engine.

    Args:
        repo_repo: RepoRepository instance.

    Returns:
        RepoPolicy instance.
    """
    return RepoPolicy(repo_repo)


async def get_write_target_policy(
    write_repo: WriteTargetRepository = Depends(get_write_target_repository),  # noqa: B008
) -> WriteTargetPolicy:
    """Get write target policy engine.

    Args:
        write_repo: WriteTargetRepository instance.

    Returns:
        WriteTargetPolicy instance.
    """
    return WriteTargetPolicy(write_repo)


async def get_llm_service_policy(
    llm_repo: LLMServiceRepository = Depends(get_llm_service_repository),  # noqa: B008
) -> LLMServicePolicy:
    """Get LLM service policy engine.

    Args:
        llm_repo: LLMServiceRepository instance.

    Returns:
        LLMServicePolicy instance.
    """
    return LLMServicePolicy(llm_repo)


async def get_llm_service_client(request: Request) -> LLMServiceClient:
    """Get LLM service HTTP client.

    Args:
        request: The current FastAPI request.

    Returns:
        LLMServiceClient instance.
    """
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Ensure lifespan has run.")

    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")

    return LLMServiceClient(
        http_client=http_client,
        default_timeout=config.llm_client_timeout,
    )


async def get_embedding_service_client(request: Request) -> EmbeddingServiceClient:
    """Get embedding service HTTP client.

    Args:
        request: The current FastAPI request.

    Returns:
        EmbeddingServiceClient instance.
    """
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Ensure lifespan has run.")

    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")

    return EmbeddingServiceClient(
        http_client=http_client,
        default_timeout=config.embedding_client_timeout,
    )


async def get_policy_engine(
    node_policy: NodePolicy = Depends(get_node_policy),  # noqa: B008
    repo_policy: RepoPolicy = Depends(get_repo_policy),  # noqa: B008
    write_target_policy: WriteTargetPolicy = Depends(get_write_target_policy),  # noqa: B008
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
) -> PolicyEngine:
    """Get the unified policy engine.

    This is the main entry point for policy validation. It combines
    all individual policies (node, repo, write target, LLM service)
    into a single validation chain with fail-closed behavior.

    Args:
        node_policy: NodePolicy instance.
        repo_policy: RepoPolicy instance.
        write_target_policy: WriteTargetPolicy instance.
        llm_service_policy: LLMServicePolicy instance.

    Returns:
        PolicyEngine instance.
    """
    return PolicyEngine(
        node_policy=node_policy,
        repo_policy=repo_policy,
        write_target_policy=write_target_policy,
        llm_service_policy=llm_service_policy,
    )


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        The global ToolRegistry instance.
    """
    from src.hub.tool_router import get_global_registry

    return get_global_registry()


async def get_policy_aware_router(
    request: Request,
    registry: ToolRegistry = Depends(get_tool_registry),  # noqa: B008
    policy_engine: PolicyEngine = Depends(get_policy_engine),  # noqa: B008
    node_repo: NodeRepository = Depends(get_node_repository),  # noqa: B008
    repo_repo: RepoRepository = Depends(get_repo_repository),  # noqa: B008
    node_client: HubNodeClient = Depends(get_node_client),  # noqa: B008
    write_target_repo: WriteTargetRepository = Depends(get_write_target_repository),  # noqa: B008
    write_target_policy: WriteTargetPolicy = Depends(get_write_target_policy),  # noqa: B008
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
    llm_client: LLMServiceClient = Depends(get_llm_service_client),  # noqa: B008
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant),  # noqa: B008
    embedding_client: EmbeddingServiceClient = Depends(get_embedding_service_client),  # noqa: B008
    issue_repo: IssueRepository = Depends(get_issue_repository),  # noqa: B008
    task_repo: TaskRepository = Depends(get_task_repository),  # noqa: B008
    doc_repo: GeneratedDocsRepository = Depends(get_generated_docs_repository),  # noqa: B008
) -> PolicyAwareToolRouter:
    """Get the policy-aware tool router.

    This router integrates policy validation with tool execution,
    implementing fail-closed behavior where policy checks must
    pass before handlers are invoked.

    Args:
        request: The current FastAPI request.
        registry: ToolRegistry instance.
        policy_engine: PolicyEngine instance.
        node_repo: NodeRepository for handler execution.
        repo_repo: RepoRepository for handler execution.
        node_client: HubNodeClient for node communication.
        write_target_repo: WriteTargetRepository for write target lookup.
        write_target_policy: WriteTargetPolicy for write access validation.
        llm_service_policy: LLMServicePolicy for LLM service validation.
        llm_client: LLMServiceClient for LLM service calls.
        qdrant_client: QdrantClientWrapper for vector search.
        embedding_client: EmbeddingServiceClient for embeddings.
        issue_repo: IssueRepository for issue storage.
        task_repo: TaskRepository for task history storage.
        doc_repo: GeneratedDocsRepository for generated doc history storage.

    Returns:
        PolicyAwareToolRouter instance.
    """
    # Import here to avoid circular dependency
    from src.hub.services.aggregation_service import AggregationService
    from src.hub.services.architecture_service import ArchitectureService
    from src.hub.services.bundle_service import BundleService
    from src.hub.services.indexing_pipeline import IndexingPipeline

    indexing_pipeline: IndexingPipeline | None = None
    bundle_service: BundleService | None = None
    aggregation_service: AggregationService | None = None
    architecture_service: ArchitectureService | None = None

    try:
        indexing_pipeline = await get_indexing_pipeline(request)
    except Exception:
        pass  # Gracefully handle if dependencies aren't ready

    try:
        bundle_service = await get_bundle_service(request)
    except Exception:
        pass  # Gracefully handle if dependencies aren't ready

    try:
        aggregation_service = await get_aggregation_service(request)
    except Exception:
        pass  # Gracefully handle if dependencies aren't ready

    try:
        architecture_service = await get_architecture_service(request)
    except Exception:
        pass  # Gracefully handle if dependencies aren't ready

    # Get task and doc repositories for observability tools
    task_repo_instance: TaskRepository | None = None
    doc_repo_instance: GeneratedDocsRepository | None = None

    try:
        task_repo_instance = await get_task_repository(request)
    except Exception:
        pass  # Gracefully handle if dependencies aren't ready

    try:
        doc_repo_instance = await get_generated_docs_repository(request)
    except Exception:
        pass  # Gracefully handle if dependencies aren't ready

    # Get http_client from app state for OpenCode adapter
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    config: HubConfig | None = request.app.state.config

    # Get or create session store
    session_store = get_session_store()

    # Create OpenCode adapter if http client available
    opencode_adapter: OpenCodeAdapter | None = None
    if http_client is not None and config is not None:
        opencode_adapter = OpenCodeAdapter(
            http_client=http_client,
            session_store=session_store,
            default_timeout=config.llm_client_timeout,
        )

    return PolicyAwareToolRouter(
        registry=registry,
        policy_engine=policy_engine,
        node_repo=node_repo,
        repo_repo=repo_repo,
        node_client=node_client,
        write_target_repo=write_target_repo,
        write_target_policy=write_target_policy,
        llm_service_policy=llm_service_policy,
        llm_client=llm_client,
        opencode_adapter=opencode_adapter,
        indexing_pipeline=indexing_pipeline,
        qdrant_client=qdrant_client,
        embedding_client=embedding_client,
        issue_repo=issue_repo,
        bundle_service=bundle_service,
        aggregation_service=aggregation_service,
        architecture_service=architecture_service,
        task_repo=task_repo_instance,
        doc_repo=doc_repo_instance,
    )


# Session and OpenCode adapter providers

# Global session store instance
_session_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Get or create the global session store.

    Returns:
        SessionStore instance.
    """
    global _session_store
    if _session_store is None:
        _session_store = SessionStore(max_history=50)
    return _session_store


async def get_opencode_adapter(
    request: Request,
    session_store: SessionStore = None,  # type: ignore[assignment]
) -> OpenCodeAdapter:
    """Get OpenCode adapter instance.

    Args:
        request: The current FastAPI request.
        session_store: SessionStore instance (injected).

    Returns:
        OpenCodeAdapter instance.
    """
    http_client: httpx.AsyncClient | None = request.app.state.http_client
    if http_client is None:
        raise RuntimeError("HTTP client not initialized. Ensure lifespan has run.")

    config: HubConfig | None = request.app.state.config
    if config is None:
        raise RuntimeError("Config not initialized. Ensure lifespan has run.")

    if session_store is None:
        session_store = get_session_store()

    return OpenCodeAdapter(
        http_client=http_client,
        session_store=session_store,
        default_timeout=config.llm_client_timeout,
    )


async def get_qdrant_client(request: Request) -> QdrantClientWrapper:
    """Get Qdrant client from app state.

    This dependency provides the Qdrant client wrapper for vector
    storage and semantic search operations.

    Args:
        request: The current FastAPI request.

    Returns:
        QdrantClientWrapper instance.

    Raises:
        RuntimeError: If Qdrant client is not initialized.
    """
    qdrant_client: QdrantClientWrapper | None = request.app.state.qdrant_client
    if qdrant_client is None:
        # Return a non-initialized client for graceful degradation
        config: HubConfig | None = request.app.state.config
        if config is None:
            raise RuntimeError("Config not initialized. Ensure lifespan has run.")
        return get_qdrant(config)
    return qdrant_client


async def get_indexing_pipeline(
    request: Request,
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),  # noqa: B008
    embedding_client: EmbeddingServiceClient = Depends(get_embedding_service_client),  # noqa: B008
    llm_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
) -> "IndexingPipeline":
    """Get indexing pipeline instance.

    Args:
        request: The current FastAPI request.
        qdrant_client: Qdrant client wrapper.
        embedding_client: Embedding service client.
        llm_service_policy: LLM service policy.

    Returns:
        Initialized IndexingPipeline.
    """
    # Import here to avoid circular imports
    from src.hub.services.indexing_pipeline import IndexingPipeline

    # Get embedding service from registry
    embedding_service = await llm_policy.get_service("embedding")
    if not embedding_service:
        raise RuntimeError("Embedding service not configured")

    return IndexingPipeline(
        qdrant_client=qdrant_client,
        embedding_client=embedding_client,
        embedding_service=embedding_service,
    )


async def get_bundle_service(
    request: Request,
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),  # noqa: B008
    embedding_client: EmbeddingServiceClient = Depends(get_embedding_service_client),  # noqa: B008
    llm_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
) -> "BundleService":
    """Get bundle service instance.

    Args:
        request: The current FastAPI request.
        qdrant_client: Qdrant client wrapper.
        embedding_client: Embedding service client.
        llm_service_policy: LLM service policy.

    Returns:
        Initialized BundleService.
    """
    # Import here to avoid circular imports
    from src.hub.services.bundle_service import BundleService

    # Get embedding service from registry
    embedding_service = await llm_policy.get_service("embedding")
    if not embedding_service:
        raise RuntimeError("Embedding service not configured")

    return BundleService(
        qdrant_client=qdrant_client,
        embedding_client=embedding_client,
        embedding_service_id=embedding_service.service_id,
    )


async def get_aggregation_service(
    request: Request,
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),  # noqa: B008
    issue_repo: "IssueRepository" = Depends(get_issue_repository),  # noqa: B008
) -> "AggregationService":
    """Get aggregation service instance.

    Args:
        request: The current FastAPI request.
        qdrant_client: Qdrant client wrapper.
        issue_repo: Issue repository for SQLite-backed issue data.

    Returns:
        Initialized AggregationService.
    """
    # Import here to avoid circular imports
    from src.hub.services.aggregation_service import AggregationService

    return AggregationService(qdrant_client=qdrant_client, issue_repo=issue_repo)


async def get_cross_repo_service(
    request: Request,
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),  # noqa: B008
    embedding_client: EmbeddingServiceClient = Depends(get_embedding_service_client),  # noqa: B008
    llm_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
    repo_repo: RepoRepository = Depends(get_repo_repository),  # noqa: B008
    relationship_repo: RelationshipRepository = Depends(get_relationship_repository),  # noqa: B008
    owner_repo: RepoOwnerRepository = Depends(get_owner_repository),  # noqa: B008
    issue_repo: IssueRepository = Depends(get_issue_repository),  # noqa: B008
) -> "CrossRepoService":
    """Get cross-repo service instance.

    Args:
        request: The current FastAPI request.
        qdrant_client: Qdrant client wrapper.
        embedding_client: Embedding service client.
        llm_policy: LLM service policy.
        repo_repo: RepoRepository instance.
        relationship_repo: RelationshipRepository instance.
        owner_repo: RepoOwnerRepository instance.
        issue_repo: IssueRepository instance for issue count queries.

    Returns:
        Initialized CrossRepoService.
    """
    # Import here to avoid circular imports
    from src.hub.services.cross_repo_service import CrossRepoService

    return CrossRepoService(
        qdrant_client=qdrant_client,
        embedding_client=embedding_client,
        llm_service_policy=llm_policy,
        repo_repo=repo_repo,
        relationship_repo=relationship_repo,
        owner_repo=owner_repo,
        issue_repo=issue_repo,
    )


async def get_relationship_service(
    request: Request,
    relationship_repo: RelationshipRepository = Depends(get_relationship_repository),  # noqa: B008
    owner_repo: RepoOwnerRepository = Depends(get_owner_repository),  # noqa: B008
    repo_repo: RepoRepository = Depends(get_repo_repository),  # noqa: B008
) -> RelationshipService:
    """Get relationship service instance.

    Args:
        request: The current FastAPI request.
        relationship_repo: RelationshipRepository instance.
        owner_repo: RepoOwnerRepository instance.
        repo_repo: RepoRepository instance.

    Returns:
        Initialized RelationshipService.
    """
    # Import here to avoid circular imports
    from src.hub.services.relationship_service import RelationshipService

    return RelationshipService(
        relationship_repo=relationship_repo,
        owner_repo=owner_repo,
        repo_repo=repo_repo,
    )


async def get_architecture_service(
    request: Request,
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),  # noqa: B008
    repo_repo: RepoRepository = Depends(get_repo_repository),  # noqa: B008
    relationship_repo: RelationshipRepository = Depends(get_relationship_repository),  # noqa: B008
    owner_repo: RepoOwnerRepository = Depends(get_owner_repository),  # noqa: B008
) -> ArchitectureService:
    """Get architecture service instance.

    Args:
        request: The current FastAPI request.
        qdrant_client: Qdrant client wrapper.
        repo_repo: RepoRepository instance.
        relationship_repo: RelationshipRepository instance.
        owner_repo: RepoOwnerRepository instance.

    Returns:
        Initialized ArchitectureService.
    """
    # Import here to avoid circular imports
    from src.hub.services.architecture_service import ArchitectureService

    return ArchitectureService(
        qdrant_client=qdrant_client,
        repo_repo=repo_repo,
        relationship_repo=relationship_repo,
        owner_repo=owner_repo,
    )


# === Task Routing Providers (SCHED-001) ===


async def get_task_routing_policy(
    task_class: TaskClass | None = None,
    preferred_service_id: str | None = None,
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
) -> TaskRoutingPolicy:
    """Get task routing policy instance.

    Args:
        task_class: The task classification for routing (defaults to CHAT).
        preferred_service_id: Optional specific service to prefer.
        llm_service_policy: LLMServicePolicy for service validation.

    Returns:
        Initialized TaskRoutingPolicy.
    """
    # Default to CHAT if not specified
    if task_class is None:
        task_class = TaskClass.CHAT

    return TaskRoutingPolicy(
        llm_service_policy=llm_service_policy,
        task_class=task_class,
        preferred_service_id=preferred_service_id,
    )


# === Distributed Scheduler Provider (SCHED-002) ===

from src.hub.policy.distributed_scheduler import DistributedScheduler


async def get_distributed_scheduler(
    task_class: TaskClass | None = None,
    preferred_service_id: str | None = None,
    node_health_service: NodeHealthService = Depends(get_node_health_service),  # noqa: B008
    node_repo: NodeRepository = Depends(get_node_repository),  # noqa: B008
    llm_service_policy: LLMServicePolicy = Depends(get_llm_service_policy),  # noqa: B008
    llm_service_repo: LLMServiceRepository = Depends(get_llm_service_repository),  # noqa: B008
) -> DistributedScheduler:
    """Get distributed scheduler instance.

    This scheduler extends TaskRoutingPolicy with node-level awareness,
    considering health, latency, and node capabilities during selection.

    Args:
        task_class: The task classification for routing (defaults to CHAT).
        preferred_service_id: Optional specific service to prefer.
        node_health_service: Health polling service.
        node_repo: Node repository.
        llm_service_policy: LLM service policy.
        llm_service_repo: LLM service repository.

    Returns:
        Initialized DistributedScheduler.
    """
    # Default to CHAT if not specified
    if task_class is None:
        task_class = TaskClass.CHAT

    # Create task routing policy
    task_routing_policy = TaskRoutingPolicy(
        llm_service_policy=llm_service_policy,
        task_class=task_class,
        preferred_service_id=preferred_service_id,
    )

    return DistributedScheduler(
        task_routing_policy=task_routing_policy,
        node_health_service=node_health_service,
        node_repository=node_repo,
        llm_service_policy=llm_service_policy,
        llm_service_repo=llm_service_repo,
    )
