"""Dependency injection providers for the GPTTalker hub."""

from collections.abc import AsyncGenerator
from typing import Any

import aiosqlite
import httpx
from fastapi import Depends, Request

from src.hub.config import HubConfig, get_hub_config
from src.hub.policy.engine import PolicyEngine
from src.hub.policy.llm_service_policy import LLMServicePolicy
from src.hub.policy.node_policy import NodePolicy
from src.hub.policy.repo_policy import RepoPolicy
from src.hub.policy.write_target_policy import WriteTargetPolicy
from src.hub.services.auth import NodeAuthHandler
from src.hub.services.node_client import HubNodeClient
from src.hub.services.node_health import NodeHealthService
from src.hub.tool_router import ToolRegistry
from src.hub.tool_routing import PolicyAwareToolRouter
from src.shared.database import DatabaseManager
from src.shared.logging import get_logger
from src.shared.repositories.llm_services import LLMServiceRepository
from src.shared.repositories.nodes import NodeRepository
from src.shared.repositories.repos import RepoRepository
from src.shared.repositories.write_targets import WriteTargetRepository

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
    registry: ToolRegistry = Depends(get_tool_registry),  # noqa: B008
    policy_engine: PolicyEngine = Depends(get_policy_engine),  # noqa: B008
) -> PolicyAwareToolRouter:
    """Get the policy-aware tool router.

    This router integrates policy validation with tool execution,
    implementing fail-closed behavior where policy checks must
    pass before handlers are invoked.

    Args:
        registry: ToolRegistry instance.
        policy_engine: PolicyEngine instance.

    Returns:
        PolicyAwareToolRouter instance.
    """
    return PolicyAwareToolRouter(registry=registry, policy_engine=policy_engine)
