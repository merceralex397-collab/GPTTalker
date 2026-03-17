"""Discovery tools for nodes and repositories."""

import time
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger
from src.shared.schemas import NodeHealthStatus

# Import type hints for forward references only
if TYPE_CHECKING:
    from src.shared.repositories.nodes import NodeRepository
    from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


async def list_nodes_handler(
    node_repo: "NodeRepository | None" = None,
) -> dict[str, Any]:
    """List all registered nodes with their health metadata.

    This tool provides discovery of all managed nodes without requiring
    a specific node_id - it's a top-level discovery tool.

    Args:
        node_repo: NodeRepository injected by the router.

    Returns:
        Dictionary with nodes list and total count.
    """
    if node_repo is None:
        return {"error": "NodeRepository not available"}
    return await list_nodes_impl(node_repo)


async def list_nodes_impl(
    node_repo: "NodeRepository",
) -> dict[str, Any]:
    """Internal implementation for list_nodes.

    Args:
        node_repo: NodeRepository instance.

    Returns:
        Node list response with health metadata.
    """
    start = int(time.time() * 1000)

    # Get all nodes
    nodes = await node_repo.list_all()

    nodes_data = []
    for node in nodes:
        # Get health metadata
        health = await node_repo.get_health(node.node_id)

        node_dict = {
            "node_id": node.node_id,
            "name": node.name,
            "hostname": node.hostname,
            "status": node.status.value,
            "last_seen": node.last_seen.isoformat() if node.last_seen else None,
            "health": {
                "health_status": (health.get("health_status", NodeHealthStatus.UNKNOWN)).value
                if health
                else NodeHealthStatus.UNKNOWN.value,
                "health_latency_ms": health.get("health_latency_ms") if health else None,
                "health_error": health.get("health_error") if health else None,
                "health_check_count": health.get("health_check_count", 0) if health else 0,
                "consecutive_failures": health.get("consecutive_failures", 0) if health else 0,
                "last_health_check": health.get("last_health_check").isoformat()
                if health and health.get("last_health_check")
                else None,
                "last_health_attempt": health.get("last_health_attempt").isoformat()
                if health and health.get("last_health_attempt")
                else None,
            }
            if health
            else None,
        }
        nodes_data.append(node_dict)

    duration = int(time.time() * 1000) - start

    logger.info("list_nodes_executed", total=len(nodes_data), duration_ms=duration)

    return {
        "nodes": nodes_data,
        "total": len(nodes_data),
    }


async def list_repos_handler(
    node_id: str | None = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """List all approved repositories.

    Optionally filter by node_id. This tool requires node access validation
    when a node_id is provided.

    Args:
        node_id: Optional node_id to filter repos by specific node.
        repo_repo: RepoRepository injected by the router.

    Returns:
        Repo list response.
    """
    if repo_repo is None:
        return {"error": "RepoRepository not available"}
    return await list_repos_impl(repo_repo, node_id)


async def list_repos_impl(
    repo_repo: "RepoRepository",
    node_id: str | None = None,
) -> dict[str, Any]:
    """Internal implementation for list_repos.

    Args:
        repo_repo: RepoRepository instance.
        node_id: Optional node_id to filter by.

    Returns:
        Repo list response.
    """
    start = int(time.time() * 1000)

    # Get repos based on filter
    if node_id:
        repos = await repo_repo.list_by_node(node_id)
    else:
        repos = await repo_repo.list_all()

    repos_data = []
    for repo in repos:
        repo_dict = {
            "repo_id": repo.repo_id,
            "name": repo.name,
            "path": repo.path,
            "node_id": repo.node_id,
            "is_indexed": repo.is_indexed,
        }
        repos_data.append(repo_dict)

    duration = int(time.time() * 1000) - start

    logger.info(
        "list_repos_executed",
        total=len(repos_data),
        filtered_by=node_id,
        duration_ms=duration,
    )

    return {
        "repos": repos_data,
        "total": len(repos_data),
        "filtered_by_node": node_id,
    }
