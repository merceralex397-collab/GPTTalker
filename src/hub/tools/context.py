"""Context retrieval and issue management tool handlers for MCP protocol."""

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import IssueIndexPayload, IssueStatus

if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.shared.repositories.issues import IssueRepository

logger = get_logger(__name__)


class GetProjectContextParams(BaseModel):
    """Parameters for get_project_context tool."""

    query: str = Field(..., description="Natural language search query")
    repo_id: str | None = Field(None, description="Filter by specific repository")
    node_id: str | None = Field(None, description="Filter by specific node")
    limit: int = Field(10, description="Maximum results", ge=1, le=100)
    score_threshold: float | None = Field(
        None, description="Minimum similarity score", ge=0.0, le=1.0
    )


class RecordIssueParams(BaseModel):
    """Parameters for record_issue tool."""

    repo_id: str = Field(..., description="Repository identifier")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    status: str = Field("open", description="Issue status")
    metadata: dict | None = Field(None, description="Additional metadata")


async def get_project_context_handler(
    params: GetProjectContextParams,
    # Injected dependencies
    qdrant_client: QdrantClientWrapper | None = None,
    embedding_client: EmbeddingServiceClient | None = None,
    llm_service_policy: "LLMServicePolicy | None" = None,
    repo_repo: Any = None,
) -> dict[str, Any]:
    """Search indexed repository content using semantic similarity.

    This tool performs semantic search over indexed files in Qdrant,
    returning results with full provenance metadata.

    Args:
        params: Tool parameters.
        qdrant_client: Qdrant client for vector search.
        embedding_client: Embedding service client for query embedding.
        llm_service_policy: LLM service policy for embedding service lookup.
        repo_repo: RepoRepository for repo access validation.

    Returns:
        Dictionary with search results and provenance metadata.
    """
    start_time = int(time.time() * 1000)

    # Validate dependencies
    if not all([qdrant_client, embedding_client, llm_service_policy]):
        logger.error("get_project_context_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Validate repo access if repo_id provided
    # For global search (repo_id is None), get accessible repos from registry
    accessible_repo_ids: list[str] | None = None

    if params.repo_id and repo_repo:
        repo = await repo_repo.get(params.repo_id)
        if not repo:
            logger.warning("get_project_context_repo_not_found", repo_id=params.repo_id)
            return {
                "success": False,
                "error": f"Repository not found: {params.repo_id}",
            }
    elif not params.repo_id and repo_repo:
        # Global search - get all accessible repos for access control
        try:
            repos = await repo_repo.list_all()
            accessible_repo_ids = [r.repo_id for r in repos]
            logger.info(
                "get_project_context_global_search",
                accessible_repos=len(accessible_repo_ids),
            )
        except Exception as e:
            logger.error("get_project_context_list_repos_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to retrieve accessible repositories",
            }

    # Get embedding service
    embedding_service = await llm_service_policy.get_service("embedding")
    if not embedding_service:
        logger.error("get_project_context_embedding_service_not_configured")
        return {
            "success": False,
            "error": "Embedding service not configured",
        }

    # Generate query embedding
    embedding_result = await embedding_client.embed(
        service=embedding_service,
        text=params.query,
        encoding_format="float",
    )

    if not embedding_result.get("success"):
        error_msg = embedding_result.get("error", "Embedding generation failed")
        logger.error("get_project_context_embedding_failed", error=error_msg)
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

    # Search Qdrant with access control
    try:
        # Use repo_ids for global search (access control), repo_id for specific search
        search_repo_ids = accessible_repo_ids if accessible_repo_ids else None
        search_results = await qdrant_client.search_files(
            query_vector=query_vector,
            repo_ids=search_repo_ids,
            repo_id=params.repo_id if not accessible_repo_ids else None,
            node_id=params.node_id,
            limit=params.limit,
            score_threshold=params.score_threshold,
        )
    except Exception as e:
        logger.error("get_project_context_search_failed", error=str(e))
        return {
            "success": False,
            "error": f"Search failed: {e}",
        }

    # Format results with provenance
    results = []
    for record in search_results:
        payload = record.payload or {}
        results.append(
            {
                "file_id": record.id,
                "repo_id": payload.get("repo_id", ""),
                "node_id": payload.get("node_id", ""),
                "path": payload.get("path", ""),
                "relative_path": payload.get("relative_path", ""),
                "filename": payload.get("filename", ""),
                "extension": payload.get("extension", ""),
                "language": payload.get("language"),
                "content_hash": payload.get("content_hash", ""),
                "size_bytes": payload.get("size_bytes", 0),
                "line_count": payload.get("line_count", 0),
                "indexed_at": payload.get("indexed_at", ""),
                "score": record.score,
                "content_preview": payload.get("content_preview"),
            }
        )

    latency_ms = int(time.time() * 1000) - start_time

    return {
        "success": True,
        "query": params.query,
        "results": results,
        "total": len(results),
        "repo_id": params.repo_id,
        "latency_ms": latency_ms,
    }


async def record_issue_handler(
    params: RecordIssueParams,
    # Injected dependencies
    qdrant_client: QdrantClientWrapper | None = None,
    embedding_client: EmbeddingServiceClient | None = None,
    llm_service_policy: "LLMServicePolicy | None" = None,
    issue_repo: "IssueRepository | None" = None,
    repo_repo: Any = None,
) -> dict[str, Any]:
    """Create and index a structured issue record.

    This tool creates an issue record in SQLite and indexes it in Qdrant
    for semantic search.

    Args:
        params: Tool parameters.
        qdrant_client: Qdrant client for issue indexing.
        embedding_client: Embedding service client for issue embedding.
        llm_service_policy: LLM service policy for embedding service lookup.
        issue_repo: IssueRepository for SQLite storage.
        repo_repo: RepoRepository for repo access validation.

    Returns:
        Dictionary with created issue details.
    """
    # Validate dependencies
    if not all([qdrant_client, embedding_client, llm_service_policy, issue_repo]):
        logger.error("record_issue_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
            "issue_id": "",
            "repo_id": params.repo_id,
            "title": params.title,
            "indexed": False,
        }

    # Validate repo access
    if repo_repo:
        repo = await repo_repo.get(params.repo_id)
        if not repo:
            logger.warning("record_issue_repo_not_found", repo_id=params.repo_id)
            return {
                "success": False,
                "error": f"Repository not found: {params.repo_id}",
                "issue_id": "",
                "repo_id": params.repo_id,
                "title": params.title,
                "indexed": False,
            }

    # Validate status
    valid_statuses = [s.value for s in IssueStatus]
    if params.status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid status: {params.status}. Valid values: {valid_statuses}",
            "issue_id": "",
            "repo_id": params.repo_id,
            "title": params.title,
            "indexed": False,
        }

    # Create issue in SQLite
    issue_id = str(uuid4())
    issue_status = IssueStatus(params.status)
    now = datetime.utcnow()

    try:
        await issue_repo.create(
            issue_id=issue_id,
            repo_id=params.repo_id,
            title=params.title,
            description=params.description,
            status=issue_status,
            metadata=params.metadata,
        )
    except Exception as e:
        logger.error("record_issue_sqlite_failed", error=str(e))
        return {
            "success": False,
            "error": f"Failed to create issue: {e}",
            "issue_id": "",
            "repo_id": params.repo_id,
            "title": params.title,
            "indexed": False,
        }

    # Index in Qdrant
    indexed = False
    embedding_service = await llm_service_policy.get_service("embedding")
    if embedding_service:
        try:
            # Generate embedding for issue content
            search_text = f"{params.title}\n{params.description}"
            embedding_result = await embedding_client.embed(
                service=embedding_service,
                text=search_text,
                encoding_format="float",
            )

            if embedding_result.get("success"):
                embeddings = embedding_result.get("embeddings", [])
                if embeddings:
                    # Create issue payload
                    issue_payload = IssueIndexPayload(
                        issue_id=issue_id,
                        repo_id=params.repo_id,
                        title=params.title,
                        description=params.description,
                        status=params.status,
                        created_at=now,
                        updated_at=now,
                        indexed_at=now,
                        metadata=params.metadata or {},
                    )

                    # Upsert to Qdrant
                    await qdrant_client.upsert_issue(
                        issue_id=issue_id,
                        vector=embeddings[0],
                        payload=issue_payload,
                    )
                    indexed = True

        except Exception as e:
            logger.warning("record_issue_qdrant_indexing_failed", error=str(e))
            # Issue was created in SQLite, just not indexed

    logger.info(
        "record_issue_success",
        issue_id=issue_id,
        repo_id=params.repo_id,
        indexed=indexed,
    )

    return {
        "success": True,
        "issue_id": issue_id,
        "repo_id": params.repo_id,
        "title": params.title,
        "indexed": indexed,
    }
