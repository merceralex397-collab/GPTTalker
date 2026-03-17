"""MCP tool handlers for architecture and landscape operations."""

from typing import Any

from src.hub.services.architecture_service import ArchitectureService
from src.shared.logging import get_logger

logger = get_logger(__name__)


async def get_architecture_map_handler(
    params: dict[str, Any],
    architecture_service: ArchitectureService,
) -> dict[str, Any]:
    """Handler for the get_architecture_map tool.

    Generates a complete architecture map with nodes, edges, language
    distribution, owner metadata, and source citations.

    Args:
        params: Tool parameters including:
            - repo_ids: Optional list of repo IDs to include
            - include_relationships: Whether to include relationships (default: True)
            - include_inferred: Whether to include inferred relationships (default: True)
            - max_depth: Maximum depth for dependency traversal (default: 3)
        architecture_service: ArchitectureService instance.

    Returns:
        Dictionary with architecture map or error.
    """
    repo_ids = params.get("repo_ids")
    include_relationships = params.get("include_relationships", True)
    include_inferred = params.get("include_inferred", True)
    max_depth = params.get("max_depth", 3)

    logger.info(
        "get_architecture_map_handler_called",
        repo_ids=repo_ids,
        include_relationships=include_relationships,
    )

    result = await architecture_service.get_architecture_map(
        repo_ids=repo_ids,
        include_relationships=include_relationships,
        include_inferred=include_inferred,
        max_depth=max_depth,
    )

    return result


async def get_repo_architecture_handler(
    params: dict[str, Any],
    architecture_service: ArchitectureService,
) -> dict[str, Any]:
    """Handler for the get_repo_architecture tool.

    Returns a focused architecture summary for a single repository,
    including language distribution, file counts, owner, and relationships.

    Args:
        params: Tool parameters including:
            - repo_id: Repository ID to get architecture for (required)
            - include_dependencies: Whether to include dependencies (default: False)
        architecture_service: ArchitectureService instance.

    Returns:
        Dictionary with single-repo architecture or error.
    """
    repo_id = params.get("repo_id")
    include_dependencies = params.get("include_dependencies", False)

    if not repo_id:
        return {
            "success": False,
            "error": "repo_id is required",
        }

    logger.info(
        "get_repo_architecture_handler_called",
        repo_id=repo_id,
    )

    result = await architecture_service.get_repo_architecture(
        repo_id=repo_id,
        include_dependencies=include_dependencies,
    )

    return result
