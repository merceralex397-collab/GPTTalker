"""Markdown write tools for controlled file delivery."""

import os
import time
from typing import TYPE_CHECKING, Any

from src.hub.policy.path_utils import PathNormalizer
from src.shared.logging import get_logger
from src.shared.models import NodeInfo

if TYPE_CHECKING:
    from src.hub.policy.write_target_policy import WriteTargetPolicy
    from src.hub.services.node_client import HubNodeClient
    from src.shared.repositories.nodes import NodeRepository
    from src.shared.repositories.write_targets import WriteTargetRepository

logger = get_logger(__name__)


def _get_extension(path: str) -> str:
    """Extract file extension from path.

    Args:
        path: File path to extract extension from.

    Returns:
        Extension with leading dot, or empty string if no extension.
    """
    _, ext = os.path.splitext(path)
    return ext.lower()


async def write_markdown_handler(
    node_id: str,
    repo_id: str,
    path: str,
    content: str,
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    write_target_repo: "WriteTargetRepository | None" = None,
    write_target_policy: "WriteTargetPolicy | None" = None,
) -> dict[str, Any]:
    """Write markdown content to an approved write target.

    This tool provides controlled markdown delivery to approved write targets.
    It validates:
    - Node exists and is accessible
    - Repository is registered and approved
    - Write target is registered and path is within allowed boundaries
    - File extension is in the allowlist for the target
    - Path doesn't contain traversal attempts

    The write is performed atomically with SHA256 verification.

    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier for the write target.
        path: File path relative to write target root (required).
        content: Markdown content to write (required).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        write_target_repo: WriteTargetRepository for write target lookup.
        write_target_policy: WriteTargetPolicy for write access validation.

    Returns:
        Dict with write result and verification metadata.
    """
    start = int(time.time() * 1000)

    # Check dependencies
    if node_client is None:
        return {"success": False, "error": "Node client not available"}
    if node_repo is None:
        return {"success": False, "error": "NodeRepository not available"}
    if write_target_repo is None:
        return {"success": False, "error": "WriteTargetRepository not available"}
    if write_target_policy is None:
        return {"success": False, "error": "WriteTargetPolicy not available"}

    # Validate inputs
    if not path:
        return {"success": False, "error": "path parameter is required"}
    if not content:
        return {"success": False, "error": "content parameter is required"}

    # Validate node exists
    node = await node_repo.get(node_id)
    if not node:
        logger.warning("write_markdown_node_not_found", node_id=node_id)
        return {"success": False, "error": f"Node not found: {node_id}"}

    # Get write targets for this repo
    try:
        write_targets = await write_target_policy.list_write_targets_for_repo(repo_id)
    except Exception as e:
        logger.warning(
            "write_markdown_write_targets_error",
            repo_id=repo_id,
            error=str(e),
        )
        return {"success": False, "error": f"Failed to get write targets: {e}"}

    if not write_targets:
        logger.warning(
            "write_markdown_no_write_targets",
            repo_id=repo_id,
            node_id=node_id,
        )
        return {
            "success": False,
            "error": f"No write targets configured for repository: {repo_id}",
        }

    # Extract extension and validate
    extension = _get_extension(path)

    # Find a matching write target that allows this extension
    allowed_target = None
    for target in write_targets:
        if extension in target.allowed_extensions:
            allowed_target = target
            break

    if not allowed_target:
        logger.warning(
            "write_markdown_extension_denied",
            repo_id=repo_id,
            path=path,
            extension=extension,
            allowed_extensions=[ext for t in write_targets for ext in t.allowed_extensions],
        )
        return {
            "success": False,
            "error": f"Extension '{extension}' not allowed for this write target. "
            f"Allowed: {[ext for t in write_targets for ext in t.allowed_extensions]}",
        }

    # Validate path doesn't contain traversal
    try:
        PathNormalizer.validate_no_traversal(path)
    except Exception as e:
        logger.warning(
            "write_markdown_path_traversal",
            path=path,
            error=str(e),
        )
        return {"success": False, "error": f"Path validation failed: {e}"}

    # Build the full write path
    full_path = os.path.join(allowed_target.path, path)

    # Normalize the path
    try:
        normalized_path = PathNormalizer.normalize(full_path, allowed_target.path)
    except Exception as e:
        logger.warning(
            "write_markdown_normalize_error",
            path=path,
            full_path=full_path,
            error=str(e),
        )
        return {"success": False, "error": f"Path normalization failed: {e}"}

    # Validate the write target allows this specific path
    try:
        await write_target_policy.validate_write_access(normalized_path, extension)
    except ValueError as e:
        logger.warning(
            "write_markdown_write_access_denied",
            path=normalized_path,
            extension=extension,
            error=str(e),
        )
        return {"success": False, "error": str(e)}

    # Call node agent to write the file
    try:
        node_info = NodeInfo(
            node_id=node.node_id,
            hostname=node.hostname,
            name=node.name,
        )
        result = await node_client.write_file(
            node=node_info,
            path=normalized_path,
            content=content,
        )
    except Exception as e:
        logger.error(
            "write_markdown_node_call_failed",
            node_id=node_id,
            repo_id=repo_id,
            path=normalized_path,
            error=str(e),
        )
        return {"success": False, "error": f"Write failed: {e}"}

    duration = int(time.time() * 1000) - start

    if result.get("success", False):
        data = result.get("data", {})

        logger.info(
            "write_markdown_success",
            node_id=node_id,
            repo_id=repo_id,
            path=normalized_path,
            bytes_written=data.get("bytes_written", 0),
            sha256_hash=data.get("sha256_hash", ""),
            duration_ms=duration,
        )

        return {
            "success": True,
            "repo_id": repo_id,
            "node_id": node_id,
            "path": normalized_path,
            "bytes_written": data.get("bytes_written", 0),
            "sha256_hash": data.get("sha256_hash", ""),
            "verified": data.get("verified", False),
            "content_hash_algorithm": data.get("content_hash_algorithm", "sha256"),
        }
    else:
        error_msg = result.get("message", "Unknown error")
        logger.warning(
            "write_markdown_failed",
            node_id=node_id,
            repo_id=repo_id,
            error=error_msg,
        )
        return {"success": False, "error": error_msg}
