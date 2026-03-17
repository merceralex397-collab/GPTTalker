"""Inspection tools for repository tree and file reading."""

import time
from datetime import datetime, timezone
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


async def inspect_repo_tree_handler(
    node_id: str,
    repo_id: str,
    path: str = "",
    max_entries: int = 100,
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """List directory contents within an approved repository.

    This tool provides directory listing within approved repos. It validates:
    - Node exists and is accessible
    - Repository is registered and approved
    - Path is within the repo boundaries (no traversal)

    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier to inspect.
        path: Directory path relative to repo root (default: root).
        max_entries: Maximum entries to return (default: 100, max: 500).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        repo_repo: RepoRepository for repo lookup.

    Returns:
        Dict with repo tree entries and metadata.
    """
    start = int(time.time() * 1000)

    # Validate inputs
    if max_entries > 500:
        max_entries = 500
    if max_entries < 1:
        max_entries = 1

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
        logger.warning("inspect_repo_tree_node_not_found", node_id=node_id)
        return {"success": False, "error": f"Node not found: {node_id}"}

    # Validate repo exists and belongs to node
    repo = await repo_repo.get(repo_id)
    if not repo:
        logger.warning("inspect_repo_tree_repo_not_found", repo_id=repo_id)
        return {"success": False, "error": f"Repository not found: {repo_id}"}

    # Verify repo belongs to the specified node
    if repo.node_id != node_id:
        logger.warning(
            "inspect_repo_tree_repo_node_mismatch",
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
    try:
        if path:
            # Validate path doesn't contain traversal attempts
            PathNormalizer.validate_no_traversal(path)
            # Normalize path relative to repo root
            normalized_path = PathNormalizer.normalize(path, repo_path)
        else:
            # Root directory - use repo path
            normalized_path = repo_path
    except PathTraversalError as e:
        logger.warning("inspect_repo_tree_path_validation_failed", path=path, error=str(e))
        return {"success": False, "error": f"Path validation failed: {e}"}

    # Call node agent to list directory
    try:
        node_info = NodeInfo(
            node_id=node.node_id,
            hostname=node.hostname,
            name=node.name,
        )
        result = await node_client.list_directory(
            node=node_info,
            path=normalized_path,
            max_entries=max_entries,
        )
    except Exception as e:
        logger.error(
            "inspect_repo_tree_node_call_failed",
            node_id=node_id,
            path=normalized_path,
            error=str(e),
        )
        return {"success": False, "error": f"Failed to list directory: {e}"}

    duration = int(time.time() * 1000) - start

    if result.get("success", False):
        entries = result.get("entries", [])
        total_count = result.get("total", len(entries))

        logger.info(
            "inspect_repo_tree_success",
            node_id=node_id,
            repo_id=repo_id,
            path=path or "/",
            entry_count=len(entries),
            duration_ms=duration,
        )

        return {
            "success": True,
            "repo_id": repo_id,
            "node_id": node_id,
            "path": path or "",
            "entries": entries,
            "total_count": total_count,
            "truncated": total_count > len(entries),
        }
    else:
        error_msg = result.get("error", "Unknown error")
        logger.warning(
            "inspect_repo_tree_failed",
            node_id=node_id,
            repo_id=repo_id,
            error=error_msg,
        )
        return {"success": False, "error": error_msg}


async def read_repo_file_handler(
    node_id: str,
    repo_id: str,
    file_path: str,
    offset: int = 0,
    limit: int | None = None,
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Read file contents from an approved repository.

    This tool provides file reading within approved repos. It validates:
    - Node exists and is accessible
    - Repository is registered and approved
    - Path is within the repo boundaries (no traversal)
    - File exists and is readable

    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier.
        file_path: File path relative to repo root.
        offset: Byte offset to start reading from (default: 0).
        limit: Maximum bytes to read (None for entire file).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        repo_repo: RepoRepository for repo lookup.

    Returns:
        Dict with file content and metadata.
    """
    start = int(time.time() * 1000)

    # Validate inputs
    if offset < 0:
        offset = 0
    if limit is not None and limit < 1:
        limit = None

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
        logger.warning("read_repo_file_node_not_found", node_id=node_id)
        return {"success": False, "error": f"Node not found: {node_id}"}

    # Validate repo exists and belongs to node
    repo = await repo_repo.get(repo_id)
    if not repo:
        logger.warning("read_repo_file_repo_not_found", repo_id=repo_id)
        return {"success": False, "error": f"Repository not found: {repo_id}"}

    # Verify repo belongs to the specified node
    if repo.node_id != node_id:
        logger.warning(
            "read_repo_file_repo_node_mismatch",
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
    try:
        # Validate path doesn't contain traversal attempts
        PathNormalizer.validate_no_traversal(file_path)
        # Normalize path relative to repo root
        normalized_path = PathNormalizer.normalize(file_path, repo_path)
    except PathTraversalError as e:
        logger.warning(
            "read_repo_file_path_validation_failed",
            file_path=file_path,
            error=str(e),
        )
        return {"success": False, "error": f"Path validation failed: {e}"}

    # Call node agent to read file
    try:
        node_info = NodeInfo(
            node_id=node.node_id,
            hostname=node.hostname,
            name=node.name,
        )
        result = await node_client.read_file(
            node=node_info,
            path=normalized_path,
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        logger.error(
            "read_repo_file_node_call_failed",
            node_id=node_id,
            path=normalized_path,
            error=str(e),
        )
        return {"success": False, "error": f"Failed to read file: {e}"}

    duration = int(time.time() * 1000) - start

    if result.get("success", False):
        content = result.get("content", "")
        size_bytes = result.get("size_bytes", 0)
        bytes_read = result.get("bytes_read", len(content))
        truncated = result.get("truncated", False)

        logger.info(
            "read_repo_file_success",
            node_id=node_id,
            repo_id=repo_id,
            file_path=file_path,
            bytes_read=bytes_read,
            duration_ms=duration,
        )

        return {
            "success": True,
            "repo_id": repo_id,
            "node_id": node_id,
            "file_path": file_path,
            "content": content,
            "encoding": "utf-8",
            "size_bytes": size_bytes,
            "truncated": truncated,
            "offset": offset,
            "bytes_read": bytes_read,
        }
    else:
        error_msg = result.get("error", "Unknown error")
        logger.warning(
            "read_repo_file_failed",
            node_id=node_id,
            repo_id=repo_id,
            file_path=file_path,
            error=error_msg,
        )
        return {"success": False, "error": error_msg}
