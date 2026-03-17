"""Policy-aware tool routing implementation.

This module provides the PolicyAwareToolRouter that integrates policy
validation with tool execution, implementing fail-closed behavior.
"""

from typing import TYPE_CHECKING, Any

from src.hub.policy.engine import PolicyEngine
from src.hub.policy.scopes import OperationScope, ValidationContext
from src.hub.tool_router import ToolDefinition, ToolRegistry
from src.hub.tool_routing.errors import (
    format_policy_error,
    format_unknown_tool_error,
)
from src.hub.tool_routing.requirements import PolicyRequirement
from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.hub.policy.write_target_policy import WriteTargetPolicy
    from src.hub.services.aggregation_service import AggregationService
    from src.hub.services.architecture_service import ArchitectureService
    from src.hub.services.bundle_service import BundleService
    from src.hub.services.embedding_client import EmbeddingServiceClient
    from src.hub.services.indexing_pipeline import IndexingPipeline
    from src.hub.services.llm_client import LLMServiceClient
    from src.hub.services.node_client import HubNodeClient
    from src.hub.services.opencode_adapter import OpenCodeAdapter
    from src.hub.services.qdrant_client import QdrantClientWrapper
    from src.shared.repositories.issues import IssueRepository
    from src.shared.repositories.nodes import NodeRepository
    from src.shared.repositories.repos import RepoRepository
    from src.shared.repositories.tasks import TaskRepository
    from src.shared.repositories.generated_docs import GeneratedDocsRepository
    from src.shared.repositories.write_targets import WriteTargetRepository

logger = get_logger(__name__)


class PolicyAwareToolRouter:
    """Tool router with integrated policy validation.

    This router wraps the basic tool routing with policy engine validation.
    All tool calls are validated against the PolicyEngine before execution,
    implementing fail-closed behavior: if policy check fails, the handler
    is not invoked.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        policy_engine: PolicyEngine,
        node_repo: "NodeRepository | None" = None,
        repo_repo: "RepoRepository | None" = None,
        node_client: "HubNodeClient | None" = None,
        write_target_repo: "WriteTargetRepository | None" = None,
        write_target_policy: "WriteTargetPolicy | None" = None,
        llm_service_policy: "LLMServicePolicy | None" = None,
        llm_client: "LLMServiceClient | None" = None,
        opencode_adapter: "OpenCodeAdapter | None" = None,
        indexing_pipeline: "IndexingPipeline | None" = None,
        qdrant_client: "QdrantClientWrapper | None" = None,
        embedding_client: "EmbeddingServiceClient | None" = None,
        issue_repo: "IssueRepository | None" = None,
        bundle_service: "BundleService | None" = None,
        aggregation_service: "AggregationService | None" = None,
        architecture_service: "ArchitectureService | None" = None,
        task_repo: "TaskRepository | None" = None,
        doc_repo: "GeneratedDocsRepository | None" = None,
    ):
        """Initialize the policy-aware tool router.

        Args:
            registry: ToolRegistry instance for tool discovery.
            policy_engine: PolicyEngine instance for access validation.
            node_repo: Optional NodeRepository for handler execution.
            repo_repo: Optional RepoRepository for handler execution.
            node_client: Optional HubNodeClient for node communication.
            write_target_repo: Optional WriteTargetRepository for write target lookup.
            write_target_policy: Optional WriteTargetPolicy for write access validation.
            llm_service_policy: Optional LLMServicePolicy for LLM service validation.
            llm_client: Optional LLMServiceClient for LLM service calls.
            opencode_adapter: Optional OpenCodeAdapter for OpenCode-specific calls.
            indexing_pipeline: Optional IndexingPipeline for repository indexing.
            qdrant_client: Optional QdrantClientWrapper for vector search.
            embedding_client: Optional EmbeddingServiceClient for embeddings.
            issue_repo: Optional IssueRepository for issue storage.
            bundle_service: Optional BundleService for context bundle operations.
            aggregation_service: Optional AggregationService for recurring issue detection.
            architecture_service: Optional ArchitectureService for architecture map generation.
        """
        self._registry = registry
        self._policy_engine = policy_engine
        self._node_repo = node_repo
        self._repo_repo = repo_repo
        self._node_client = node_client
        self._write_target_repo = write_target_repo
        self._write_target_policy = write_target_policy
        self._llm_service_policy = llm_service_policy
        self._llm_client = llm_client
        self._opencode_adapter = opencode_adapter
        self._indexing_pipeline = indexing_pipeline
        self._qdrant_client = qdrant_client
        self._embedding_client = embedding_client
        self._issue_repo = issue_repo
        self._bundle_service = bundle_service
        self._aggregation_service = aggregation_service
        self._architecture_service = architecture_service
        self._task_repo = task_repo
        self._doc_repo = doc_repo

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry.

        Returns:
            The ToolRegistry instance.
        """
        return self._registry

    async def route_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Route tool call with policy validation.

        This method:
        1. Checks if the tool is registered
        2. Extracts policy requirements from the tool definition
        3. Runs policy validation based on requirements
        4. Executes the handler if validation passes
        5. Returns MCP-formatted error if validation fails

        Args:
            tool_name: Name of the tool to invoke.
            parameters: Parameters for the tool.
            trace_id: Optional trace ID for request correlation.

        Returns:
            Tool execution result or MCP error response.
        """
        log_context = {
            "tool_name": tool_name,
            "trace_id": trace_id,
            "param_keys": list(parameters.keys()) if parameters else [],
        }

        # Step 1: Check if tool is registered
        definition = self._registry.get_definition(tool_name)
        if not definition:
            logger.warning("tool_not_found", **log_context)
            return format_unknown_tool_error(tool_name, trace_id)

        # Step 2: Check if policy is required for this tool
        policy_req = self._get_policy_requirement(definition)

        if policy_req is None:
            # No policy required - direct execution
            return await self._execute_handler(
                definition.handler,
                parameters,
                trace_id,
                log_context,
            )

        # Step 3: Build validation context
        context = ValidationContext(
            scope=policy_req.scope,
            trace_id=trace_id,
            caller=tool_name,
        )

        # Step 4: Run policy validation
        validation_error = await self._validate_policy(
            policy_req,
            parameters,
            context,
            log_context,
        )

        if validation_error:
            logger.warning("policy_validation_failed", **log_context, error=validation_error)
            return format_policy_error(
                reason=validation_error,
                trace_id=trace_id,
                details={"tool": tool_name, "parameters": self._sanitize_params(parameters)},
            )

        # Step 5: Execute handler
        logger.info("policy_validation_passed", **log_context)
        return await self._execute_handler(
            definition.handler,
            parameters,
            trace_id,
            log_context,
        )

    def _get_policy_requirement(
        self,
        definition: ToolDefinition,
    ) -> PolicyRequirement | None:
        """Extract policy requirements from tool definition.

        Args:
            definition: Tool definition to extract requirements from.

        Returns:
            PolicyRequirement if defined, None only if explicitly opted out.

        Note:
            Default behavior is fail-closed: if no explicit policy is set,
            a basic node validation requirement is returned to ensure unknown
            tools are not allowed through without checks.
        """
        # Check for explicit policy field (CORE-006 addition)
        if hasattr(definition, "policy") and definition.policy is not None:
            return definition.policy

        # Check legacy requires_policy_check field - explicit opt-out
        if hasattr(definition, "requires_policy_check"):
            if not definition.requires_policy_check:
                # Explicitly opted out of policy - return None
                return None

        # Default: require basic node validation for fail-closed behavior
        # Unknown tools without explicit policy must go through basic validation
        # This maintains the security posture from CORE-005
        from src.hub.tool_routing.requirements import READ_NODE_REQUIREMENT

        return READ_NODE_REQUIREMENT

    async def _validate_policy(
        self,
        policy_req: PolicyRequirement,
        parameters: dict[str, Any],
        context: ValidationContext,
        log_context: dict[str, Any],
    ) -> str | None:
        """Run policy validation based on requirements.

        Args:
            policy_req: Policy requirements for the tool.
            parameters: Tool call parameters.
            context: Validation context.
            log_context: Logging context.

        Returns:
            Error message if validation failed, None if passed.
        """
        # Validate node access if required
        if policy_req.requires_node:
            node_id = policy_req.extract_node_id(parameters)
            if node_id:
                error = await self._validate_node(node_id, policy_req.scope, log_context)
                if error:
                    return error

        # Validate repo access if required
        if policy_req.requires_repo:
            repo_id = policy_req.extract_repo_id(parameters)
            if repo_id:
                error = await self._validate_repo(repo_id, log_context)
                if error:
                    return error

        # Validate write target if required
        if policy_req.requires_write_target:
            path = policy_req.extract_path(parameters)
            extension = policy_req.extract_extension(parameters)
            if path:
                error = await self._validate_write_target(path, extension or "", log_context)
                if error:
                    return error

        # Validate LLM service if required
        if policy_req.requires_llm_service:
            service_id = policy_req.extract_service_id(parameters)
            if service_id:
                error = await self._validate_llm_service(service_id, log_context)
                if error:
                    return error

        return None

    async def _validate_node(
        self,
        node_id: str,
        scope: OperationScope,
        log_context: dict[str, Any],
    ) -> str | None:
        """Validate node access.

        Args:
            node_id: Node identifier to validate.
            scope: Operation scope.
            log_context: Logging context.

        Returns:
            Error message if validation failed, None if passed.
        """
        try:
            if scope == OperationScope.WRITE:
                result = await self._policy_engine.validate_node_write(node_id)
            else:
                result = await self._policy_engine.validate_node_read(node_id)

            if not result.approved:
                return f"Node access denied: {result.rejection_reason}"
        except Exception as e:
            logger.error("node_validation_error", **log_context, error=str(e))
            return f"Node validation error: {e}"

        return None

    async def _validate_repo(
        self,
        repo_id: str,
        log_context: dict[str, Any],
    ) -> str | None:
        """Validate repo access.

        Args:
            repo_id: Repo identifier to validate.
            log_context: Logging context.

        Returns:
            Error message if validation failed, None if passed.
        """
        try:
            await self._policy_engine.validate_repo_read(repo_id)
        except ValueError as e:
            return f"Repository access denied: {e}"
        except Exception as e:
            logger.error("repo_validation_error", **log_context, error=str(e))
            return f"Repository validation error: {e}"

        return None

    async def _validate_write_target(
        self,
        path: str,
        extension: str,
        log_context: dict[str, Any],
    ) -> str | None:
        """Validate write target access.

        Args:
            path: Path to write to.
            extension: File extension.
            log_context: Logging context.

        Returns:
            Error message if validation failed, None if passed.
        """
        try:
            await self._policy_engine.validate_write_target(path, extension)
        except ValueError as e:
            return f"Write target denied: {e}"
        except Exception as e:
            logger.error("write_target_validation_error", **log_context, error=str(e))
            return f"Write target validation error: {e}"

        return None

    async def _validate_llm_service(
        self,
        service_id: str,
        log_context: dict[str, Any],
    ) -> str | None:
        """Validate LLM service access.

        Args:
            service_id: Service identifier to validate.
            log_context: Logging context.

        Returns:
            Error message if validation failed, None if passed.
        """
        try:
            await self._policy_engine.validate_llm_service(service_id)
        except ValueError as e:
            return f"LLM service denied: {e}"
        except Exception as e:
            logger.error("llm_service_validation_error", **log_context, error=str(e))
            return f"LLM service validation error: {e}"

        return None

    async def _execute_handler(
        self,
        handler: Any,
        parameters: dict[str, Any],
        trace_id: str | None,
        log_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the tool handler.

        Args:
            handler: Tool handler function.
            parameters: Tool parameters.
            trace_id: Trace ID for correlation.
            log_context: Logging context.

        Returns:
            Tool execution result.
        """
        import inspect

        # Build execution kwargs - pass repositories if handler accepts them
        exec_kwargs = dict(parameters)
        if self._node_repo is not None:
            # Check if handler signature accepts node_repo
            sig = inspect.signature(handler)
            if "node_repo" in sig.parameters:
                exec_kwargs["node_repo"] = self._node_repo
        if self._repo_repo is not None:
            # Check if handler signature accepts repo_repo
            sig = inspect.signature(handler)
            if "repo_repo" in sig.parameters:
                exec_kwargs["repo_repo"] = self._repo_repo
        if self._node_client is not None:
            # Check if handler signature accepts node_client
            sig = inspect.signature(handler)
            if "node_client" in sig.parameters:
                exec_kwargs["node_client"] = self._node_client
        if self._write_target_repo is not None:
            # Check if handler signature accepts write_target_repo
            sig = inspect.signature(handler)
            if "write_target_repo" in sig.parameters:
                exec_kwargs["write_target_repo"] = self._write_target_repo
        if self._write_target_policy is not None:
            # Check if handler signature accepts write_target_policy
            sig = inspect.signature(handler)
            if "write_target_policy" in sig.parameters:
                exec_kwargs["write_target_policy"] = self._write_target_policy
        if self._llm_service_policy is not None:
            # Check if handler signature accepts llm_service_policy
            sig = inspect.signature(handler)
            if "llm_service_policy" in sig.parameters:
                exec_kwargs["llm_service_policy"] = self._llm_service_policy
        if self._llm_client is not None:
            # Check if handler signature accepts llm_client
            sig = inspect.signature(handler)
            if "llm_client" in sig.parameters:
                exec_kwargs["llm_client"] = self._llm_client
        if self._opencode_adapter is not None:
            # Check if handler signature accepts opencode_adapter
            sig = inspect.signature(handler)
            if "opencode_adapter" in sig.parameters:
                exec_kwargs["opencode_adapter"] = self._opencode_adapter
        if self._indexing_pipeline is not None:
            # Check if handler signature accepts indexing_pipeline
            sig = inspect.signature(handler)
            if "indexing_pipeline" in sig.parameters:
                exec_kwargs["indexing_pipeline"] = self._indexing_pipeline
        if self._qdrant_client is not None:
            # Check if handler signature accepts qdrant_client
            sig = inspect.signature(handler)
            if "qdrant_client" in sig.parameters:
                exec_kwargs["qdrant_client"] = self._qdrant_client
        if self._embedding_client is not None:
            # Check if handler signature accepts embedding_client
            sig = inspect.signature(handler)
            if "embedding_client" in sig.parameters:
                exec_kwargs["embedding_client"] = self._embedding_client
        if self._issue_repo is not None:
            # Check if handler signature accepts issue_repo
            sig = inspect.signature(handler)
            if "issue_repo" in sig.parameters:
                exec_kwargs["issue_repo"] = self._issue_repo
        if self._task_repo is not None:
            # Check if handler signature accepts task_repo
            sig = inspect.signature(handler)
            if "task_repo" in sig.parameters:
                exec_kwargs["task_repo"] = self._task_repo
        if self._doc_repo is not None:
            # Check if handler signature accepts doc_repo
            sig = inspect.signature(handler)
            if "doc_repo" in sig.parameters:
                exec_kwargs["doc_repo"] = self._doc_repo
        if self._bundle_service is not None:
            # Check if handler signature accepts bundle_service
            sig = inspect.signature(handler)
            if "bundle_service" in sig.parameters:
                exec_kwargs["bundle_service"] = self._bundle_service
        if self._aggregation_service is not None:
            # Check if handler signature accepts aggregation_service
            sig = inspect.signature(handler)
            if "aggregation_service" in sig.parameters:
                exec_kwargs["aggregation_service"] = self._aggregation_service
        if self._architecture_service is not None:
            # Check if handler signature accepts architecture_service
            sig = inspect.signature(handler)
            if "architecture_service" in sig.parameters:
                exec_kwargs["architecture_service"] = self._architecture_service

        try:
            result = await handler(**exec_kwargs)
            logger.info("tool_execution_success", **log_context)
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            logger.error("tool_execution_failed", **log_context, error=str(e))
            return {
                "success": False,
                "error": str(e),
            }

    def _sanitize_params(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters for logging (remove sensitive data).

        Args:
            parameters: Original parameters.

        Returns:
            Sanitized parameters with sensitive data removed.
        """
        # List of parameter keys that might contain sensitive data
        sensitive_keys = {"api_key", "password", "secret", "token", "credential"}

        sanitized = {}
        for key, value in parameters.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized
