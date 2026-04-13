"""MCP protocol handling for the hub."""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from fastapi import FastAPI

from src.hub.tool_router import get_global_registry
from src.hub.tool_routing import PolicyAwareToolRouter
from src.hub.transport.mcp import (
    format_tool_list,
    format_tool_response,
    parse_tool_call,
)
from src.shared.logging import get_logger
from src.shared.models import TaskOutcome

if TYPE_CHECKING:
    from src.shared.database import DatabaseManager

logger = get_logger(__name__)


class MCPProtocolHandler:
    """Handles MCP protocol communication between ChatGPT and the hub.

    This handler routes tool calls to registered handlers with integrated
    policy validation via PolicyAwareToolRouter.
    """

    def __init__(self, router: PolicyAwareToolRouter | None = None):
        """Initialize the MCP protocol handler.

        Args:
            router: Optional PolicyAwareToolRouter. Creates one if not provided.
        """
        self._router = router

    async def initialize(self, app: FastAPI) -> None:
        """Pre-build the policy-aware router using app state.

        This method must be called during lifespan startup, before the app
        starts accepting requests. It bypasses FastAPI's dependency injection
        by accessing app.state directly, avoiding the TypeError that occurs
        when calling FastAPI dependencies outside a request context.

        Args:
            app: The FastAPI application instance with populated state.
        """
        if self._router is not None:
            return  # Already initialized

        registry = get_global_registry()

        # Access app.state directly to build dependencies without FastAPI DI
        db_manager = getattr(app.state, "db_manager", None)
        http_client = getattr(app.state, "http_client", None)
        config = getattr(app.state, "config", None)
        qdrant_client = getattr(app.state, "qdrant_client", None)
        embedding_client = getattr(app.state, "embedding_client", None)

        # Build repositories using db_manager from app.state
        from src.hub.policy.engine import PolicyEngine
        from src.hub.policy.llm_service_policy import LLMServicePolicy
        from src.hub.policy.node_policy import NodePolicy
        from src.hub.policy.repo_policy import RepoPolicy
        from src.hub.policy.write_target_policy import WriteTargetPolicy
        from src.hub.services.auth import NodeAuthHandler
        from src.hub.services.embedding_client import EmbeddingServiceClient
        from src.hub.services.llm_client import LLMServiceClient
        from src.hub.services.node_client import HubNodeClient
        from src.hub.services.node_health import NodeHealthService
        from src.hub.services.qdrant_client import QdrantClientWrapper, get_qdrant_client
        from src.shared.repositories.issues import IssueRepository
        from src.shared.repositories.llm_services import LLMServiceRepository
        from src.shared.repositories.nodes import NodeRepository
        from src.shared.repositories.repos import RepoRepository
        from src.shared.repositories.tasks import TaskRepository
        from src.shared.repositories.write_targets import WriteTargetRepository

        # Build repositories
        node_repo = NodeRepository(db_manager) if db_manager else None
        repo_repo = RepoRepository(db_manager) if db_manager else None
        write_target_repo = WriteTargetRepository(db_manager) if db_manager else None
        llm_service_repo = LLMServiceRepository(db_manager) if db_manager else None
        issue_repo = IssueRepository(db_manager) if db_manager else None
        task_repo_instance = TaskRepository(db_manager) if db_manager else None

        # Build node health service
        auth_handler = NodeAuthHandler(config.node_client_api_key) if config else None
        node_health_service = (
            NodeHealthService(
                node_repo=node_repo,
                http_client=http_client,
                auth_handler=auth_handler,
            )
            if node_repo and http_client
            else None
        )

        # Build services
        node_policy = NodePolicy(node_repo, node_health_service) if node_repo else None
        repo_policy = RepoPolicy(repo_repo) if repo_repo else None
        write_target_policy = WriteTargetPolicy(write_target_repo) if write_target_repo else None
        llm_service_policy = LLMServicePolicy(llm_service_repo) if llm_service_repo else None

        # Build policy engine
        policy_engine = None
        if all(
            p is not None
            for p in [node_policy, repo_policy, write_target_policy, llm_service_policy]
        ):
            policy_engine = PolicyEngine(
                node_policy=node_policy,
                repo_policy=repo_policy,
                write_target_policy=write_target_policy,
                llm_service_policy=llm_service_policy,
            )

        # Build HTTP clients
        node_client = None
        llm_client = None
        if http_client and config:
            auth_handler = NodeAuthHandler(config.node_client_api_key)
            node_client = HubNodeClient(
                http_client=http_client,
                auth_handler=auth_handler,
                default_timeout=config.node_client_timeout,
                connect_timeout=config.node_client_connect_timeout,
            )
            llm_client = LLMServiceClient(
                http_client=http_client,
                default_timeout=config.llm_client_timeout,
            )

        # Get qdrant client
        if qdrant_client is None and config is not None:
            qdrant_client = get_qdrant_client(config)

        # Get embedding client from app.state or build new one
        if embedding_client is None and http_client and config:
            embedding_client = EmbeddingServiceClient(
                http_client=http_client,
                default_timeout=config.embedding_client_timeout,
            )

        # Build optional services with graceful fallback
        indexing_pipeline = None
        bundle_service = None
        aggregation_service = None
        architecture_service = None
        doc_repo_instance = None

        try:
            from src.hub.services.indexing_pipeline import IndexingPipeline

            if qdrant_client and embedding_client and llm_service_policy:
                try:
                    embedding_service = await llm_service_policy.get_service("embedding")
                    if embedding_service:
                        indexing_pipeline = IndexingPipeline(
                            qdrant_client=qdrant_client,
                            embedding_client=embedding_client,
                            embedding_service=embedding_service,
                        )
                except Exception:
                    pass
        except ImportError:
            pass

        try:
            from src.hub.services.bundle_service import BundleService

            if qdrant_client and embedding_client and llm_service_policy:
                try:
                    embedding_service = await llm_service_policy.get_service("embedding")
                    if embedding_service:
                        bundle_service = BundleService(
                            qdrant_client=qdrant_client,
                            embedding_client=embedding_client,
                            embedding_service_id=embedding_service.service_id,
                        )
                except Exception:
                    pass
        except ImportError:
            pass

        try:
            from src.hub.services.aggregation_service import AggregationService

            if qdrant_client and issue_repo:
                aggregation_service = AggregationService(
                    qdrant_client=qdrant_client,
                    issue_repo=issue_repo,
                )
        except ImportError:
            pass

        try:
            from src.hub.services.architecture_service import ArchitectureService

            if qdrant_client and repo_repo:
                from src.shared.repositories.relationships import (
                    RelationshipRepository,
                    RepoOwnerRepository,
                )

                relationship_repo = RelationshipRepository(db_manager) if db_manager else None
                owner_repo = RepoOwnerRepository(db_manager) if db_manager else None
                if relationship_repo and owner_repo:
                    architecture_service = ArchitectureService(
                        qdrant_client=qdrant_client,
                        repo_repo=repo_repo,
                        relationship_repo=relationship_repo,
                        owner_repo=owner_repo,
                    )
        except ImportError:
            pass

        try:
            from src.shared.repositories.generated_docs import GeneratedDocsRepository

            doc_repo_instance = GeneratedDocsRepository(db_manager) if db_manager else None
        except ImportError:
            pass

        # Build the router
        self._router = PolicyAwareToolRouter(
            registry=registry,
            policy_engine=policy_engine,
            node_repo=node_repo,
            repo_repo=repo_repo,
            node_client=node_client,
            write_target_repo=write_target_repo,
            write_target_policy=write_target_policy,
            llm_service_policy=llm_service_policy,
            llm_client=llm_client,
            opencode_adapter=None,  # Built on-demand per request
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

        logger.info("mcp_router_initialized", policy_engine_available=policy_engine is not None)

    async def _ensure_router(self) -> PolicyAwareToolRouter:
        """Ensure router is initialized (async).

        Returns:
            PolicyAwareToolRouter instance.

        Raises:
            RuntimeError: If router is not set and cannot be created.
        """
        if self._router is None:
            # This should not happen if initialize() was called during lifespan.
            # Fall back to a minimal router for backward compatibility.
            registry = get_global_registry()
            from src.hub.policy.engine import PolicyEngine

            self._router = PolicyAwareToolRouter(
                registry=registry,
                policy_engine=PolicyEngine(
                    node_policy=None,
                    repo_policy=None,
                    write_target_policy=None,
                    llm_service_policy=None,
                ),
            )
        return self._router

    async def handle_tool_call(
        self,
        tool_name: str,
        parameters: dict,
        trace_id: str | None = None,
        db_manager: "DatabaseManager | None" = None,
    ) -> dict[str, Any]:
        """
        Handle an MCP tool call from ChatGPT.

        Args:
            tool_name: Name of the tool to invoke
            parameters: Parameters for the tool
            trace_id: Optional trace ID for request correlation
            db_manager: Optional DatabaseManager for task persistence

        Returns:
            Tool response in MCP format
        """
        import time

        start_time = int(time.time() * 1000)

        # Generate trace_id if not provided
        if trace_id is None:
            trace_id = str(uuid4())

        # Ensure router is available
        router = await self._ensure_router()

        # Check if tool is registered
        if not router.registry.is_registered(tool_name):
            logger.warning(
                "unknown_tool_requested",
                tool_name=tool_name,
                trace_id=trace_id,
            )
            return format_tool_response(
                result=None,
                trace_id=trace_id,
                duration_ms=int(time.time() * 1000) - start_time,
                error=f"Unknown tool: {tool_name}",
            )

        # Route to handler with policy validation
        result = await router.route_tool(
            tool_name=tool_name,
            parameters=parameters,
            trace_id=trace_id,
        )

        duration_ms = int(time.time() * 1000) - start_time

        # Persist task to database if db_manager is available
        if db_manager is not None:
            try:
                from src.shared.repositories.tasks import TaskRepository

                task_repo = TaskRepository(db_manager)
                # Determine success from nested result structure
                is_success = result.get("success", False)
                outcome = TaskOutcome.SUCCESS if is_success else TaskOutcome.ERROR
                error_msg = result.get("error") if not is_success else None

                await task_repo.create(
                    task_id=uuid4(),
                    tool_name=tool_name,
                    caller="mcp",
                    outcome=outcome,
                    duration_ms=duration_ms,
                    trace_id=trace_id,
                    error=error_msg,
                )
            except Exception as e:
                # Log but don't fail the tool call if task persistence fails
                logger.warning(
                    "task_persistence_failed",
                    tool_name=tool_name,
                    trace_id=trace_id,
                    error=str(e),
                )

        if result.get("success"):
            return format_tool_response(
                result=result.get("result"),
                trace_id=trace_id,
                duration_ms=duration_ms,
            )
        else:
            return format_tool_response(
                result=None,
                trace_id=trace_id,
                duration_ms=duration_ms,
                error=result.get("error", "Tool execution failed"),
            )

    async def list_tools(self) -> dict[str, Any]:
        """List all available MCP tools.

        Returns:
            MCP-formatted tool list response.
        """
        router = await self._ensure_router()
        tools = router.registry.list_tools()
        return format_tool_list(tools)

    async def handle_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Handle a raw MCP request.

        Parses the request, routes to the appropriate handler,
        and formats the response.

        Args:
            request_data: Raw MCP request data (JSON-RPC 2.0 format).

        Returns:
            MCP-formatted response.
        """
        method = request_data.get("method")
        message_id = request_data.get("id")
        trace_id = request_data.get("trace_id")

        if method == "tools/call":
            # Parse tool call
            parsed = parse_tool_call(request_data)
            return await self.handle_tool_call(
                tool_name=parsed["tool_name"],
                parameters=parsed["parameters"],
                trace_id=parsed["trace_id"] or trace_id,
            )
        elif method == "tools/list":
            return await self.list_tools()
        else:
            # Unknown method
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }
