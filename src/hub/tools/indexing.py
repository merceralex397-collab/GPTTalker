"""Index repository tool handler for MCP protocol."""

from typing import Any

from pydantic import BaseModel, Field

from src.hub.services.indexing_pipeline import IndexingPipeline
from src.hub.services.indexing_pipeline import IndexMode as IndexMode
from src.shared.logging import get_logger
from src.shared.models import NodeInfo

logger = get_logger(__name__)


class IndexRepoParams(BaseModel):
    """Parameters for the index_repo tool."""

    repo_id: str = Field(..., description="Repository identifier to index")
    node_id: str | None = Field(
        None, description="Node ID (auto-detected from repo if not provided)"
    )
    mode: str = Field(
        "incremental",
        description="Indexing mode: 'incremental' (skip unchanged) or 'full' (reindex all)",
    )
    force: bool = Field(False, description="Force full reindex even in incremental mode")


async def index_repo_handler(
    params: IndexRepoParams,
    # Injected dependencies
    indexing_pipeline: IndexingPipeline | None = None,
    repo_repo: Any = None,
    node_repo: Any = None,
    node_client: Any = None,
) -> dict[str, Any]:
    """Index a repository's content into Qdrant.

    This tool reads repository files, generates embeddings, and stores
    them in Qdrant with content-hash tracking for idempotent reindexing.

    Args:
        params: Tool parameters.
        indexing_pipeline: IndexingPipeline instance.
        repo_repo: RepoRepository for repo lookup.
        node_repo: NodeRepository for node lookup.
        node_client: HubNodeClient for node communication.

    Returns:
        Dictionary with indexing results.
    """
    # Validate dependencies
    if not all([indexing_pipeline, repo_repo, node_repo, node_client]):
        logger.error("index_repo_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Get repo
    repo = await repo_repo.get(params.repo_id)
    if not repo:
        logger.warning("index_repo_repo_not_found", repo_id=params.repo_id)
        return {
            "success": False,
            "error": f"Repository not found: {params.repo_id}",
        }

    # Get node
    node_id = params.node_id or repo.node_id
    node = await node_repo.get(node_id)
    if not node:
        logger.warning("index_repo_node_not_found", node_id=node_id)
        return {
            "success": False,
            "error": f"Node not found: {node_id}",
        }

    # Build node info
    node_info = NodeInfo(
        node_id=node.node_id,
        name=node.name,
        hostname=node.hostname,
        status=node.status,
    )

    # Determine mode
    mode = IndexMode.FULL if params.mode == "full" else IndexMode.INCREMENTAL
    if params.force:
        mode = IndexMode.FULL

    logger.info(
        "index_repo_starting",
        repo_id=repo.repo_id,
        node_id=node_id,
        mode=mode.value,
    )

    # Run indexing
    result = await indexing_pipeline.index_repo(
        repo=repo,
        node_client=node_client,
        node_info=node_info,
        mode=mode,
    )

    # Update repo indexed status
    if result.success:
        await repo_repo.mark_indexed(repo.repo_id)
        logger.info(
            "index_repo_marked_indexed",
            repo_id=repo.repo_id,
        )

    return {
        "success": result.success,
        "repo_id": result.repo_id,
        "indexed_count": result.indexed_count,
        "skipped_count": result.skipped_count,
        "deleted_count": result.deleted_count,
        "duration_ms": result.duration_ms,
        "error": result.error,
    }
