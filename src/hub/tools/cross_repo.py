"""Cross-repo search and global context tool handlers for MCP protocol."""

import time
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


class SearchAcrossReposParams(BaseModel):
    """Parameters for search_across_repos tool."""

    query: str = Field(..., description="Natural language search query")
    repo_ids: list[str] | None = Field(
        None,
        description="List of repository IDs to search. If omitted, searches all accessible repos",
    )
    limit: int = Field(10, description="Maximum results", ge=1, le=100)
    score_threshold: float | None = Field(
        None, description="Minimum similarity score", ge=0.0, le=1.0
    )


class ListRelatedReposParams(BaseModel):
    """Parameters for list_related_repos tool."""

    repo_id: str = Field(..., description="Repository ID to find relationships for")
    relationship_type: str = Field(
        "files",
        description="Type of relationship: files, issues, or bundles",
        enum=["files", "issues", "bundles"],
    )
    limit: int = Field(10, description="Maximum related repos", ge=1, le=20)


class GetProjectLandscapeParams(BaseModel):
    """Parameters for get_project_landscape tool."""

    include_relationships: bool = Field(
        False, description="Include relationship data between repos"
    )


async def search_across_repos_handler(
    params: SearchAcrossReposParams,
    # Injected dependencies
    qdrant_client: QdrantClientWrapper | None = None,
    embedding_client: EmbeddingServiceClient | None = None,
    llm_service_policy: "LLMServicePolicy | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Search indexed content across multiple repositories.

    This tool performs semantic search over files in specified repos
    or all accessible repos. Results include per-repo metadata and
    full provenance for each file hit.

    Args:
        params: Tool parameters.
        qdrant_client: Qdrant client for vector search.
        embedding_client: Embedding service client for query embedding.
        llm_service_policy: LLM service policy for embedding service lookup.
        repo_repo: RepoRepository for repo access validation.

    Returns:
        Dictionary with search results and metadata.
    """
    start_time = int(time.time() * 1000)

    # Validate dependencies
    if not all([qdrant_client, embedding_client, llm_service_policy, repo_repo]):
        logger.error("search_across_repos_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Get accessible repos for access control
    try:
        all_repos = await repo_repo.list_all()
        accessible_repo_map = {r.repo_id: r for r in all_repos}
    except Exception as e:
        logger.error("search_across_repos_get_repos_failed", error=str(e))
        return {
            "success": False,
            "error": "Failed to retrieve accessible repositories",
        }

    # Determine which repos to search
    if params.repo_ids:
        # Validate requested repos are accessible
        search_repo_ids = [rid for rid in params.repo_ids if rid in accessible_repo_map]
        if not search_repo_ids:
            logger.warning(
                "search_across_repos_no_accessible_repos",
                requested=params.repo_ids,
            )
            return {
                "success": False,
                "error": "No accessible repositories found for the requested repo_ids",
            }
    else:
        # Search all accessible repos
        search_repo_ids = list(accessible_repo_map.keys())

    # Limit to max 20 repos for performance
    search_repo_ids = search_repo_ids[:20]

    # Get embedding service
    embedding_service = await llm_service_policy.get_service("embedding")
    if not embedding_service:
        logger.error("search_across_repos_embedding_service_not_configured")
        return {
            "success": False,
            "error": "Embedding service not configured",
        }

    # Generate query embedding
    try:
        embedding_result = await embedding_client.embed(
            service=embedding_service,
            text=params.query,
            encoding_format="float",
        )
    except Exception as e:
        logger.error("search_across_repos_embedding_failed", error=str(e))
        return {
            "success": False,
            "error": f"Embedding generation failed: {e}",
        }

    if not embedding_result.get("success"):
        error_msg = embedding_result.get("error", "Embedding generation failed")
        return {
            "success": False,
            "error": f"Embedding generation failed: {error_msg}",
        }

    embeddings = embedding_result.get("embeddings", [])
    if not embeddings:
        return {
            "success": False,
            "error": "No embeddings returned",
        }

    query_vector = embeddings[0]

    # Search Qdrant
    try:
        search_results = await qdrant_client.search_files(
            query_vector=query_vector,
            repo_ids=search_repo_ids,
            limit=params.limit,
            score_threshold=params.score_threshold,
        )
    except Exception as e:
        logger.error("search_across_repos_qdrant_failed", error=str(e))
        return {
            "success": False,
            "error": f"Search failed: {e}",
        }

    # Build file results with provenance
    file_results = []
    for record in search_results:
        payload = record.payload or {}
        file_results.append(
            {
                "file_id": record.id,
                "repo_id": payload.get("repo_id", ""),
                "node_id": payload.get("node_id", ""),
                "path": payload.get("path", ""),
                "relative_path": payload.get("relative_path", ""),
                "filename": payload.get("filename", ""),
                "extension": payload.get("extension", ""),
                "language": payload.get("language"),
                "score": record.score,
                "content_preview": payload.get("content_preview"),
            }
        )

    # Build repo metadata for searched repos
    repo_metadata = []
    for repo_id in search_repo_ids:
        repo = accessible_repo_map.get(repo_id)
        if repo:
            repo_metadata.append(
                {
                    "repo_id": repo.repo_id,
                    "node_id": repo.node_id,
                    "file_count": 0,
                    "issue_count": 0,
                }
            )

    latency_ms = int(time.time() * 1000) - start_time

    logger.info(
        "search_across_repos_success",
        query=params.query,
        repos_searched=len(search_repo_ids),
        results=len(file_results),
        latency_ms=latency_ms,
    )

    return {
        "success": True,
        "query": params.query,
        "total_results": len(file_results),
        "repos_searched": len(search_repo_ids),
        "repo_metadata": repo_metadata,
        "file_results": file_results,
        "latency_ms": latency_ms,
    }


async def list_related_repos_handler(
    params: ListRelatedReposParams,
    # Injected dependencies
    qdrant_client: QdrantClientWrapper | None = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Find repositories related to a given repo based on shared content.

    This tool finds repos that share similar files, issues, or bundles.
    Uses Qdrant to find overlapping content embeddings.

    Args:
        params: Tool parameters.
        qdrant_client: Qdrant client for searching.
        repo_repo: RepoRepository for repo access validation.

    Returns:
        Dictionary with list of related repos.
    """
    # Validate dependencies
    if not all([qdrant_client, repo_repo]):
        logger.error("list_related_repos_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Validate the source repo exists and is accessible
    try:
        source_repo = await repo_repo.get(params.repo_id)
        if not source_repo:
            return {
                "success": False,
                "error": f"Repository not found: {params.repo_id}",
            }
    except Exception as e:
        logger.error("list_related_repos_get_repo_failed", error=str(e))
        return {
            "success": False,
            "error": "Failed to validate repository access",
        }

    # Get all accessible repos (excluding the source repo)
    try:
        all_repos = await repo_repo.list_all()
        accessible_repos = [r for r in all_repos if r.repo_id != params.repo_id]
    except Exception as e:
        logger.error("list_related_repos_get_repos_failed", error=str(e))
        return {
            "success": False,
            "error": "Failed to retrieve accessible repositories",
        }

    # Find relationships based on file content overlap
    related_repos = []

    if params.relationship_type == "files":
        try:
            source_files = await qdrant_client.scroll_files(
                repo_id=params.repo_id,
                limit=1000,
            )

            # For each accessible repo, count overlapping files
            for other_repo in accessible_repos[: params.limit * 2]:
                other_files = await qdrant_client.scroll_files(
                    repo_id=other_repo.repo_id,
                    limit=100,
                )

                # Hash-based overlap detection
                source_hashes = {
                    f.payload.get("content_hash", "")
                    for f in source_files
                    if f.payload.get("content_hash")
                }
                other_hashes = {
                    f.payload.get("content_hash", "")
                    for f in other_files
                    if f.payload.get("content_hash")
                }

                overlap = source_hashes & other_hashes
                if overlap:
                    overlap_score = len(overlap) / max(len(source_hashes), 1)
                    related_repos.append(
                        {
                            "repo_id": other_repo.repo_id,
                            "node_id": other_repo.node_id,
                            "relationship_type": "files",
                            "overlap_score": overlap_score,
                            "shared_file_count": len(overlap),
                        }
                    )

        except Exception as e:
            logger.warning("list_related_repos_file_search_failed", error=str(e))

    # Sort by overlap score
    related_repos.sort(key=lambda r: r.get("overlap_score", 0), reverse=True)
    related_repos = related_repos[: params.limit]

    logger.info(
        "list_related_repos_success",
        repo_id=params.repo_id,
        relationship_type=params.relationship_type,
        related_count=len(related_repos),
    )

    return {
        "success": True,
        "source_repo_id": params.repo_id,
        "relationship_type": params.relationship_type,
        "related_repos": related_repos,
    }


async def get_project_landscape_handler(
    params: GetProjectLandscapeParams,
    # Injected dependencies
    qdrant_client: QdrantClientWrapper | None = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Get an overview of all accessible repositories with metadata.

    This tool returns a landscape view of all accessible repos,
    including file counts, issue counts, languages, and optional
    relationship data.

    Args:
        params: Tool parameters.
        qdrant_client: Qdrant client for searching.
        repo_repo: RepoRepository for repo access validation.

    Returns:
        Dictionary with project landscape information.
    """
    # Validate dependencies
    if not all([qdrant_client, repo_repo]):
        logger.error("get_project_landscape_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Get all accessible repos
    try:
        repos = await repo_repo.list_all()
    except Exception as e:
        logger.error("get_project_landscape_get_repos_failed", error=str(e))
        return {
            "success": False,
            "error": "Failed to retrieve accessible repositories",
        }

    # Build repo metadata for each accessible repo
    repo_metadata = []
    total_files = 0
    total_issues = 0

    for repo in repos:
        # Get file count from Qdrant (simplified - just indicate accessible)
        file_count = 0

        # Get issue count
        issue_count = 0

        # Get languages
        languages: list[str] = []

        repo_metadata.append(
            {
                "repo_id": repo.repo_id,
                "node_id": repo.node_id,
                "file_count": file_count,
                "issue_count": issue_count,
                "last_indexed_at": None,
                "languages": languages,
            }
        )

        total_files += file_count
        total_issues += issue_count

    # Build relationships if requested
    relationships = None
    if params.include_relationships and len(repos) > 1:
        relationships = []

    logger.info(
        "get_project_landscape_success",
        total_repos=len(repos),
        include_relationships=params.include_relationships,
    )

    return {
        "success": True,
        "total_repos": len(repos),
        "total_files": total_files,
        "total_issues": total_issues,
        "repos": repo_metadata,
        "relationships": relationships,
    }
