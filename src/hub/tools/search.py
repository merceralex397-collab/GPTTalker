"""Search tools for repository text search."""

import time
from typing import TYPE_CHECKING, Any

from src.hub.policy.path_utils import PathNormalizer
from src.shared.exceptions import PathTraversalError
from src.shared.logging import get_logger
from src.shared.models import NodeInfo

if TYPE_CHECKING:
    from src.hub.services.node_client import HubNodeClient
    from src.shared.repositories.nodes import NodeRepository
    from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


async def search_repo_handler(
    node_id: str,
    repo_id: str,
    pattern: str,
    path: str = "",
    include_patterns: list[str] | None = None,
    max_results: int = 1000,
    timeout: int = 60,
    mode: str = "text",
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Search for pattern in files within an approved repository.

    This tool provides text search within approved repos using bounded ripgrep
    execution. It validates:
    - Node exists and is accessible
    - Repository is registered and approved
    - Path is within the repo boundaries (no traversal)
    - Pattern is provided and valid

    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier to search.
        pattern: Regex pattern to search for.
        path: Directory path relative to repo root (default: root).
        include_patterns: File patterns to include (e.g., ["*.py", "*.md"]).
        max_results: Maximum matches to return (default: 1000).
        timeout: Search timeout in seconds (default: 60).
        mode: Search mode - "text" for content, "path" for filenames, "symbol" for identifiers (default: text).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        repo_repo: RepoRepository for repo lookup.

    Returns:
        Dict with search results and metadata.
    """
    start = int(time.time() * 1000)

    # Validate inputs
    if not pattern:
        return {"success": False, "error": "Search pattern is required"}

    # Validate mode parameter
    valid_modes = ["text", "path", "symbol"]
    if mode not in valid_modes:
        return {"success": False, "error": f"Invalid mode: {mode}. Must be one of: {valid_modes}"}

    if max_results > 1000:
        max_results = 1000
    if max_results < 1:
        max_results = 1

    if timeout > 120:
        timeout = 120
    if timeout < 1:
        timeout = 1

    # Check dependencies
    if node_client is None:
        return {"success": False, "error": "Node client not available"}
    if node_repo is None:
        return {"success": False, "error": "NodeRepository not available"}
    if repo_repo is None:
        return {"success": False, "error": "RepoRepository not available"}

    # Validate node exists
    node = await node_repo.get(node_id)
    if not node:
        logger.warning("search_repo_node_not_found", node_id=node_id)
        return {"success": False, "error": f"Node not found: {node_id}"}

    # Validate repo exists and belongs to node
    repo = await repo_repo.get(repo_id)
    if not repo:
        logger.warning("search_repo_repo_not_found", repo_id=repo_id)
        return {"success": False, "error": f"Repository not found: {repo_id}"}

    # Verify repo belongs to the specified node
    if repo.node_id != node_id:
        logger.warning(
            "search_repo_repo_node_mismatch",
            repo_id=repo_id,
            repo_node_id=repo.node_id,
            requested_node_id=node_id,
        )
        return {
            "success": False,
            "error": f"Repository {repo_id} is not on node {node_id}",
        }

    # Get the repo's base path
    repo_path = repo.path

    # Validate and normalize the path
    search_path = repo_path
    if path:
        try:
            # Validate path doesn't contain traversal attempts
            PathNormalizer.validate_no_traversal(path)
            # Normalize path relative to repo root
            search_path = PathNormalizer.normalize(path, repo_path)
        except PathTraversalError as e:
            logger.warning(
                "search_repo_path_validation_failed",
                path=path,
                error=str(e),
            )
            return {"success": False, "error": f"Path validation failed: {e}"}

    # Call node agent to search
    try:
        node_info = NodeInfo(
            node_id=node.node_id,
            hostname=node.hostname,
            name=node.name,
        )
        result = await node_client.search(
            node=node_info,
            directory=search_path,
            pattern=pattern,
            include_patterns=include_patterns,
            max_results=max_results,
            timeout=timeout,
            mode=mode,
        )
    except Exception as e:
        logger.error(
            "search_repo_node_call_failed",
            node_id=node_id,
            repo_id=repo_id,
            path=search_path,
            error=str(e),
        )
        return {"success": False, "error": f"Search failed: {e}"}

    duration = int(time.time() * 1000) - start

    if result.get("success", False):
        # Extract inner payload from OperationResponse envelope
        payload = result.get("data", {})
        matches = payload.get("matches", [])
        match_count = payload.get("match_count", 0)
        files_searched = payload.get("files_searched", 0)

        logger.info(
            "search_repo_success",
            node_id=node_id,
            repo_id=repo_id,
            path=path or "/",
            pattern=pattern,
            match_count=match_count,
            duration_ms=duration,
        )

        return {
            "success": True,
            "repo_id": repo_id,
            "node_id": node_id,
            "path": path or "",
            "pattern": pattern,
            "mode": mode,
            "matches": matches,
            "match_count": match_count,
            "files_searched": files_searched,
            "truncated": match_count >= max_results,
        }
    else:
        error_msg = result.get("error", "Unknown error")
        logger.warning(
            "search_repo_failed",
            node_id=node_id,
            repo_id=repo_id,
            error=error_msg,
        )
        return {"success": False, "error": error_msg}
