"""App lifecycle management for the GPTTalker hub."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.hub.config import get_hub_config
from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.qdrant_client import create_qdrant_client, get_qdrant_client
from src.hub.services.tunnel_manager import TunnelManager
from src.shared.database import initialize_database
from src.shared.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events.

    This lifespan context manager handles:
    1. Initializing logging from config
    2. Initializing database connection
    3. Running migrations
    4. Storing manager references in app state for dependency injection
    5. On shutdown: closing database connections and logging shutdown

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the application during its runtime.
    """
    # Get configuration
    config = get_hub_config()

    # Step 1: Initialize logging
    setup_logging(level=config.log_level, format_type=config.log_format)
    logger.info("hub_starting", config={"host": config.host, "port": config.port})

    # Step 2: Initialize database
    db_manager = await initialize_database()

    # Step 3: Store references in app state for dependency injection
    app.state.db_manager = db_manager
    app.state.config = config

    # Step 4: Initialize HTTP client for hub-to-node communication
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            config.node_client_timeout,
            connect=config.node_client_connect_timeout,
        ),
        limits=httpx.Limits(
            max_connections=config.node_client_pool_max_connections,
            max_keepalive_connections=config.node_client_pool_max_keepalive,
        ),
    )

    logger.info(
        "http_client_initialized",
        timeout=config.node_client_timeout,
        connect_timeout=config.node_client_connect_timeout,
        max_connections=config.node_client_pool_max_connections,
    )

    # Step 5: Initialize embedding client
    app.state.embedding_client = EmbeddingServiceClient(
        http_client=app.state.http_client,
        default_timeout=config.embedding_client_timeout,
    )

    logger.info(
        "embedding_client_initialized",
        timeout=config.embedding_client_timeout,
    )

    # Step 6: Initialize Qdrant client (fail-open: log warning but continue if unavailable)
    try:
        app.state.qdrant_client = await create_qdrant_client(config)
        logger.info(
            "qdrant_client_initialized",
            host=config.qdrant_host,
            port=config.qdrant_port,
        )
    except Exception as e:
        # Fail-open: log warning but allow hub to start
        logger.warning(
            "qdrant_client_init_failed_continuing",
            error=str(e),
            host=config.qdrant_host,
            port=config.qdrant_port,
        )
        # Create uninitialized client for graceful degradation
        app.state.qdrant_client = get_qdrant_client(config)

    logger.info("hub_ready", db_path=config.database_url)

    # Step 7: Initialize ngrok tunnel manager
    # Initialize to None first to ensure attribute exists for shutdown check
    app.state.tunnel_manager: TunnelManager | None = None

    tunnel_manager = TunnelManager(config)
    app.state.tunnel_manager = tunnel_manager

    # Start tunnel if enabled
    tunnel_started = await tunnel_manager.start()
    if tunnel_started:
        logger.info(
            "ngrok_tunnel_integration_ready",
            enabled=config.ngrok_enabled,
            external=tunnel_manager._is_external
            if hasattr(tunnel_manager, "_is_external")
            else False,
        )
    else:
        logger.info(
            "ngrok_tunnel_not_started",
            enabled=config.ngrok_enabled,
        )

    # Step 8a: Register all MCP tools BEFORE initializing MCP handler
    # Note: @app.on_event("startup") in main.py is deprecated when lifespan= is set.
    # Tools must be registered before mcp_handler.initialize() builds the router.
    from src.hub.tool_router import get_global_registry
    from src.hub.tools import register_all_tools

    registry = get_global_registry()
    register_all_tools(registry)
    logger.info("mcp_tools_registered", tool_count=registry.tool_count)

    # Step 8: Pre-build MCP router using app state (RC-1 fix)
    # This avoids the FastAPI DI anti-pattern where get_policy_engine()
    # was called directly in _ensure_router() without a request context,
    # causing TypeError: missing 'request' argument on every tool call.
    from src.hub.handlers import mcp_handler

    await mcp_handler.initialize(app)
    logger.info("mcp_handler_initialized")

    # Step 8b: Hydrate node health for all registered nodes before accepting traffic
    # (fail-open: log warning but continue if health check fails)
    try:
        from src.hub.services.auth import NodeAuthHandler
        from src.hub.services.node_health import NodeHealthService
        from src.shared.repositories.nodes import NodeRepository

        node_repo = NodeRepository(db_manager)
        auth_handler = NodeAuthHandler(config.node_client_api_key)

        node_health_service = NodeHealthService(
            http_client=app.state.http_client,
            node_repo=node_repo,
            auth_handler=auth_handler,
        )
        await node_health_service.check_all_nodes()
        logger.info("node_health_hydrated")
    except Exception as e:
        logger.warning(
            "node_health_hydration_failed_continuing",
            error=str(e),
            exc_info=e,
        )

    # Yield control to the application
    yield

    # --- Shutdown phase ---

    logger.info("hub_shutting_down")

    # Stop tunnel manager (graceful shutdown)
    if app.state.tunnel_manager is not None:
        await app.state.tunnel_manager.stop()

    # Close Qdrant client
    if app.state.qdrant_client is not None:
        try:
            await app.state.qdrant_client.close()
            logger.info("qdrant_client_closed")
        except Exception as e:
            logger.warning("qdrant_client_close_error", error=str(e))

    # Close HTTP client
    if app.state.http_client is not None:
        await app.state.http_client.aclose()
        logger.info("http_client_closed")

    # Close database connection
    if app.state.db_manager is not None:
        await app.state.db_manager.close()
        logger.info("database_connection_closed")

    logger.info("hub_stopped")
