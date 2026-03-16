"""Policy requirements for tool routing.

This module defines the policy requirement declarations that tools use
to declare their security and access control needs at registration time.
"""

from dataclasses import dataclass
from typing import Any, TypedDict

from src.hub.policy.scopes import OperationScope


class ToolContext(TypedDict):
    """Context passed to all tool handlers.

    Attributes:
        trace_id: Optional trace ID for request correlation.
        policy_result: Pre-validated policy result if policy check passed.
    """

    trace_id: str | None
    policy_result: dict[str, Any] | None


class ToolResult(TypedDict):
    """Standard tool result structure.

    Attributes:
        success: Whether the tool executed successfully.
        data: The result data if successful.
        error: Error message if failed.
        trace_id: Trace ID for correlation.
    """

    success: bool
    data: Any | None
    error: str | None
    trace_id: str | None


@dataclass
class PolicyRequirement:
    """Declares what policy checks a tool requires.

    This dataclass is attached to tool definitions to declare the
    security and access control requirements. The PolicyAwareToolRouter
    uses these declarations to validate tool calls before execution.

    Attributes:
        scope: The operation scope (READ, WRITE, EXECUTE).
        requires_node: Whether node access must be validated.
        requires_repo: Whether repo access must be validated (if repo_id param exists).
        requires_write_target: Whether write target must be validated (for writes).
        requires_llm_service: Whether LLM service must be validated (for LLM calls).
        node_param: Parameter name for node ID.
        repo_param: Parameter name for repo ID.
        path_param: Parameter name for file path.
        extension_param: Parameter name for file extension.
        service_param: Parameter name for LLM service ID.
    """

    scope: OperationScope
    requires_node: bool = True
    requires_repo: bool = False
    requires_write_target: bool = False
    requires_llm_service: bool = False
    node_param: str = "node_id"
    repo_param: str = "repo_id"
    path_param: str = "path"
    extension_param: str = "extension"
    service_param: str = "service_id"

    def extract_node_id(self, parameters: dict[str, Any]) -> str | None:
        """Extract node ID from tool parameters.

        Args:
            parameters: Tool call parameters.

        Returns:
            Node ID if present in parameters, None otherwise.
        """
        return parameters.get(self.node_param)

    def extract_repo_id(self, parameters: dict[str, Any]) -> str | None:
        """Extract repo ID from tool parameters.

        Args:
            parameters: Tool call parameters.

        Returns:
            Repo ID if present in parameters, None otherwise.
        """
        return parameters.get(self.repo_param)

    def extract_path(self, parameters: dict[str, Any]) -> str | None:
        """Extract file path from tool parameters.

        Args:
            parameters: Tool call parameters.

        Returns:
            Path if present in parameters, None otherwise.
        """
        return parameters.get(self.path_param)

    def extract_extension(self, parameters: dict[str, Any]) -> str | None:
        """Extract file extension from tool parameters.

        Args:
            parameters: Tool call parameters.

        Returns:
            Extension if present in parameters, None otherwise.
        """
        return parameters.get(self.extension_param)

    def extract_service_id(self, parameters: dict[str, Any]) -> str | None:
        """Extract LLM service ID from tool parameters.

        Args:
            parameters: Tool call parameters.

        Returns:
            Service ID if present in parameters, None otherwise.
        """
        return parameters.get(self.service_param)


# Pre-defined policy requirements for common tool types

# Read operation requiring node and optionally repo access
READ_REPO_REQUIREMENT = PolicyRequirement(
    scope=OperationScope.READ,
    requires_node=True,
    requires_repo=True,
)

# Read operation requiring node only
READ_NODE_REQUIREMENT = PolicyRequirement(
    scope=OperationScope.READ,
    requires_node=True,
    requires_repo=False,
)

# Write operation requiring node and write target validation
WRITE_REQUIREMENT = PolicyRequirement(
    scope=OperationScope.WRITE,
    requires_node=True,
    requires_write_target=True,
)

# LLM operation requiring service validation
LLM_REQUIREMENT = PolicyRequirement(
    scope=OperationScope.READ,  # LLM calls are treated as read operations
    requires_node=False,
    requires_llm_service=True,
)

# No policy required - for tools that don't need access control
NO_POLICY_REQUIREMENT = PolicyRequirement(
    scope=OperationScope.READ,
    requires_node=False,
    requires_repo=False,
    requires_write_target=False,
    requires_llm_service=False,
)


def create_read_requirement(
    requires_repo: bool = False,
    node_param: str = "node_id",
    repo_param: str = "repo_id",
) -> PolicyRequirement:
    """Create a policy requirement for read operations.

    Args:
        requires_repo: Whether repo validation is required.
        node_param: Name of node_id parameter.
        repo_param: Name of repo_id parameter.

    Returns:
        PolicyRequirement configured for read operations.
    """
    return PolicyRequirement(
        scope=OperationScope.READ,
        requires_node=True,
        requires_repo=requires_repo,
        node_param=node_param,
        repo_param=repo_param,
    )


def create_write_requirement(
    node_param: str = "node_id",
    path_param: str = "path",
    extension_param: str = "extension",
) -> PolicyRequirement:
    """Create a policy requirement for write operations.

    Args:
        node_param: Name of node_id parameter.
        path_param: Name of path parameter.
        extension_param: Name of extension parameter.

    Returns:
        PolicyRequirement configured for write operations.
    """
    return PolicyRequirement(
        scope=OperationScope.WRITE,
        requires_node=True,
        requires_write_target=True,
        node_param=node_param,
        path_param=path_param,
        extension_param=extension_param,
    )


def create_llm_requirement(
    service_param: str = "service_id",
) -> PolicyRequirement:
    """Create a policy requirement for LLM operations.

    Args:
        service_param: Name of service_id parameter.

    Returns:
        PolicyRequirement configured for LLM operations.
    """
    return PolicyRequirement(
        scope=OperationScope.READ,  # LLM calls treated as read
        requires_node=False,
        requires_llm_service=True,
        service_param=service_param,
    )
