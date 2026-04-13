"""Git operations tools for repository git status."""

import time
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger
from src.shared.models import NodeInfo

if TYPE_CHECKING:
    from src.hub.services.node_client import HubNodeClient
    from src.shared.repositories.nodes import NodeRepository
    from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


async def git_status_handler(
    node_id: str,
    repo_id: str,
    timeout: int = 30,
    node_client: "HubNodeClient | None" = None,
    node_repo: "NodeRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Get git status for an approved repository.

    This tool provides read-only git status for approved repositories.
    It validates:
    - Node exists and is accessible
    - Repository is registered and approved
    - Repository path is a valid git repository

    This tool only exposes read-only git operations:
    - git status --porcelain (clean/modified/staged/untracked)
    - git branch --show-current (current branch)
    - git rev-list (ahead/behind count relative to remote)

    Args:
        node_id: Target node identifier.
        repo_id: Repository identifier.
        timeout: Git operation timeout in seconds (default: 30).
        node_client: HubNodeClient for node communication.
        node_repo: NodeRepository for node lookup.
        repo_repo: RepoRepository for repo lookup.

    Returns:
        Dict with git status information.
    """
    start = int(time.time() * 1000)

    # Validate inputs
    if timeout > 60:
        timeout = 60
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
        logger.warning("git_status_node_not_found", node_id=node_id)
        return {"success": False, "error": f"Node not found: {node_id}"}

    # Validate repo exists and belongs to node
    repo = await repo_repo.get(repo_id)
    if not repo:
        logger.warning("git_status_repo_not_found", repo_id=repo_id)
        return {"success": False, "error": f"Repository not found: {repo_id}"}

    # Verify repo belongs to the specified node
    if repo.node_id != node_id:
        logger.warning(
            "git_status_repo_node_mismatch",
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

    # Call node agent to get git status
    try:
        node_info = NodeInfo(
            node_id=node.node_id,
            hostname=node.hostname,
            name=node.name,
        )
        result = await node_client.git_status(
            node=node_info,
            repo_path=repo_path,
            timeout=timeout,
        )
        # Unwrap OperationResponse envelope
        payload = result.get("data", {}) if isinstance(result, dict) else {}
    except Exception as e:
        logger.error(
            "git_status_node_call_failed",
            node_id=node_id,
            repo_id=repo_id,
            path=repo_path,
            error=str(e),
        )
        return {"success": False, "error": f"Git status failed: {e}"}

    duration = int(time.time() * 1000) - start

    if result.get("success", False):
        is_clean = payload.get("is_clean", False)
        staged_count = payload.get("staged_count", 0)
        modified_count = payload.get("modified_count", 0)
        untracked_count = payload.get("untracked_count", 0)

        logger.info(
            "git_status_success",
            node_id=node_id,
            repo_id=repo_id,
            branch=payload.get("branch", "unknown"),
            is_clean=is_clean,
            duration_ms=duration,
        )

        return {
            "success": True,
            "repo_id": repo_id,
            "node_id": node_id,
            "path": repo_path,
            "branch": payload.get("branch", "unknown"),
            "is_clean": is_clean,
            "is_dirty": not is_clean,
            "staged": payload.get("staged", []),
            "staged_count": staged_count,
            "modified": payload.get("modified", []),
            "modified_count": modified_count,
            "untracked": payload.get("untracked", []),
            "untracked_count": untracked_count,
            "ahead": payload.get("ahead", 0),
            "behind": payload.get("behind", 0),
            "recent_commits": payload.get("recent_commits", []),
        }
    else:
        error_msg = result.get("error", "Unknown error")
        logger.warning(
            "git_status_failed",
            node_id=node_id,
            repo_id=repo_id,
            error=error_msg,
        )
        return {"success": False, "error": error_msg}
