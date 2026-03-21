"""Cross-repo search and global context service for GPTTalker."""

import time
from typing import TYPE_CHECKING, Any

from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import (
    CrossRepoSearchResult,
    FileSearchHit,
    LandscapeMetadata,
    LandscapeSource,
    ProjectLandscape,
    RelatedRepo,
    RepoMetadata,
    RepoOwner,
)
from src.shared.repositories.repos import RepoRepository

if TYPE_CHECKING:
    from src.hub.policy.llm_service_policy import LLMServicePolicy
    from src.shared.repositories.issues import IssueRepository

logger = get_logger(__name__)


class CrossRepoService:
    """Service for cross-repo search and global context operations.

    This service provides high-level operations for searching across
    multiple repositories, finding related repos, and generating
    project landscape views.
    """

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
        embedding_client: EmbeddingServiceClient,
        llm_service_policy: "LLMServicePolicy",
        repo_repo: RepoRepository,
        relationship_repo: "Any" = None,
        owner_repo: "Any" = None,
        issue_repo: "IssueRepository | None" = None,
    ) -> None:
        """Initialize the cross-repo service.

        Args:
            qdrant_client: Qdrant client for vector search.
            embedding_client: Embedding service client.
            llm_service_policy: LLM service policy for embedding service lookup.
            repo_repo: Repository for repo access validation.
            relationship_repo: Optional relationship repository for explicit relationships.
            owner_repo: Optional owner repository for owner metadata.
            issue_repo: Optional issue repository for issue count queries.
        """
        self.qdrant_client = qdrant_client
        self.embedding_client = embedding_client
        self.llm_service_policy = llm_service_policy
        self.repo_repo = repo_repo
        self.relationship_repo = relationship_repo
        self.owner_repo = owner_repo
        self.issue_repo = issue_repo

    async def search_across_repos(
        self,
        query: str,
        repo_ids: list[str] | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Search indexed content across multiple repositories.

        This method performs semantic search over files in specified repos
        or all accessible repos. Results include full provenance metadata.

        Args:
            query: Natural language search query.
            repo_ids: Optional list of repository IDs to search. If None,
                     searches all accessible repos.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0 to 1.0).

        Returns:
            Dictionary with search results and metadata.
        """
        start_time = int(time.time() * 1000)

        # Get accessible repos for access control
        try:
            all_repos = await self.repo_repo.list_all()
            accessible_repo_map = {r.repo_id: r for r in all_repos}
        except Exception as e:
            logger.error("cross_repo_search_get_repos_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to retrieve accessible repositories",
            }

        # Determine which repos to search
        if repo_ids:
            # Validate requested repos are accessible
            search_repo_ids = [rid for rid in repo_ids if rid in accessible_repo_map]
            if not search_repo_ids:
                logger.warning(
                    "cross_repo_search_no_accessible_repos",
                    requested=repo_ids,
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
        embedding_service = await self.llm_service_policy.get_service("embedding")
        if not embedding_service:
            logger.error("cross_repo_search_embedding_service_not_configured")
            return {
                "success": False,
                "error": "Embedding service not configured",
            }

        # Generate query embedding
        try:
            embedding_result = await self.embedding_client.embed(
                service=embedding_service,
                text=query,
                encoding_format="float",
            )
        except Exception as e:
            logger.error("cross_repo_search_embedding_failed", error=str(e))
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
            search_results = await self.qdrant_client.search_files(
                query_vector=query_vector,
                repo_ids=search_repo_ids,
                limit=limit,
                score_threshold=score_threshold,
            )
        except Exception as e:
            logger.error("cross_repo_search_qdrant_failed", error=str(e))
            return {
                "success": False,
                "error": f"Search failed: {e}",
            }

        # Build file results with provenance
        file_results: list[FileSearchHit] = []
        for record in search_results:
            payload = record.payload or {}
            file_results.append(
                FileSearchHit(
                    file_id=record.id,
                    repo_id=payload.get("repo_id", ""),
                    node_id=payload.get("node_id", ""),
                    path=payload.get("path", ""),
                    relative_path=payload.get("relative_path", ""),
                    filename=payload.get("filename", ""),
                    extension=payload.get("extension", ""),
                    language=payload.get("language"),
                    score=record.score,
                    content_preview=payload.get("content_preview"),
                )
            )

        # Build repo metadata for searched repos
        repo_metadata: list[RepoMetadata] = []
        for repo_id in search_repo_ids:
            repo = accessible_repo_map.get(repo_id)
            if repo:
                # Get real file count from Qdrant
                file_count = 0
                try:
                    file_count = await self.qdrant_client.count_files_by_repo(repo_id)
                except Exception as e:
                    logger.warning(
                        "cross_repo_search_file_count_failed",
                        repo_id=repo_id,
                        error=str(e),
                    )

                # Get real issue count from IssueRepository
                issue_count = 0
                if self.issue_repo:
                    try:
                        issue_count = await self.issue_repo.count_by_repo(repo_id)
                    except Exception as e:
                        logger.warning(
                            "cross_repo_search_issue_count_failed",
                            repo_id=repo_id,
                            error=str(e),
                        )

                repo_metadata.append(
                    RepoMetadata(
                        repo_id=repo.repo_id,
                        node_id=repo.node_id,
                        file_count=file_count,
                        issue_count=issue_count,
                    )
                )

        latency_ms = int(time.time() * 1000) - start_time

        result = CrossRepoSearchResult(
            query=query,
            total_results=len(file_results),
            repos_searched=len(search_repo_ids),
            repo_metadata=repo_metadata,
            file_results=file_results,
            latency_ms=latency_ms,
        )

        logger.info(
            "cross_repo_search_success",
            query=query,
            repos_searched=len(search_repo_ids),
            results=len(file_results),
            latency_ms=latency_ms,
        )

        return {
            "success": True,
            **result.model_dump(),
        }

    async def list_related_repos(
        self,
        repo_id: str,
        relationship_type: str = "files",
        limit: int = 10,
    ) -> dict[str, Any]:
        """Find repositories related to a given repo based on shared content.

        This method finds repos that share similar files, issues, or bundles
        using Qdrant to find overlapping content embeddings.

        Args:
            repo_id: Repository ID to find relationships for.
            relationship_type: Type of relationship: files, issues, or bundles.
            limit: Maximum number of related repos to return.

        Returns:
            Dictionary with list of related repos.
        """
        # Validate the source repo exists and is accessible
        try:
            source_repo = await self.repo_repo.get(repo_id)
            if not source_repo:
                return {
                    "success": False,
                    "error": f"Repository not found: {repo_id}",
                }
        except Exception as e:
            logger.error("list_related_repos_get_repo_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to validate repository access",
            }

        # Get all accessible repos (excluding the source repo)
        try:
            all_repos = await self.repo_repo.list_all()
            accessible_repos = [r for r in all_repos if r.repo_id != repo_id]
        except Exception as e:
            logger.error("list_related_repos_get_repos_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to retrieve accessible repositories",
            }

        # For now, implement a simplified relationship finder
        # In a full implementation, this would use Qdrant to find repos with
        # similar embeddings based on shared file content
        related_repos: list[RelatedRepo] = []

        # Get file data for the source repo to find overlaps
        if relationship_type == "files":
            try:
                source_files = await self.qdrant_client.scroll_files(
                    repo_id=repo_id,
                    limit=1000,
                )

                # For each accessible repo, count overlapping files
                for other_repo in accessible_repos[:limit]:
                    other_files = await self.qdrant_client.scroll_files(
                        repo_id=other_repo.repo_id,
                        limit=100,
                    )

                    # Simple hash-based overlap detection
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
                            RelatedRepo(
                                repo_id=other_repo.repo_id,
                                node_id=other_repo.node_id,
                                relationship_type="files",
                                overlap_score=overlap_score,
                                shared_file_count=len(overlap),
                            )
                        )

            except Exception as e:
                logger.warning("list_related_repos_file_search_failed", error=str(e))
                # Continue with empty results rather than failing

        # Sort by overlap score
        related_repos.sort(key=lambda r: r.overlap_score, reverse=True)
        related_repos = related_repos[:limit]

        logger.info(
            "list_related_repos_success",
            repo_id=repo_id,
            relationship_type=relationship_type,
            related_count=len(related_repos),
        )

        return {
            "success": True,
            "source_repo_id": repo_id,
            "relationship_type": relationship_type,
            "related_repos": [r.model_dump() for r in related_repos],
        }

    async def get_project_landscape(
        self,
        include_relationships: bool = False,
    ) -> dict[str, Any]:
        """Get an overview of all accessible repositories with metadata.

        This method returns a landscape view of all accessible repos,
        including file counts, issue counts, languages, optional
        relationship data, owner metadata, and source citations.

        Args:
            include_relationships: Whether to include relationship data.

        Returns:
            Dictionary with project landscape information.
        """
        from datetime import datetime

        # Get all accessible repos
        try:
            repos = await self.repo_repo.list_all()
        except Exception as e:
            logger.error("get_project_landscape_get_repos_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to retrieve accessible repositories",
            }

        # Get owners if available
        owners_map: dict[str, RepoOwner] = {}
        if self.owner_repo:
            try:
                owners_map = await self.owner_repo.list_all()
            except Exception as e:
                logger.warning("get_project_landscape_get_owners_failed", error=str(e))

        # Build repo metadata for each accessible repo with owner info
        repo_metadata: list[RepoMetadata] = []
        total_files = 0
        total_issues = 0
        sources: list[LandscapeSource] = []

        for repo in repos:
            # Get real file count from Qdrant
            file_count = 0
            try:
                file_count = await self.qdrant_client.count_files_by_repo(repo.repo_id)
            except Exception as e:
                logger.warning(
                    "get_project_landscape_file_count_failed",
                    repo_id=repo.repo_id,
                    error=str(e),
                )

            # Get real issue count from IssueRepository
            issue_count = 0
            if self.issue_repo:
                try:
                    issue_count = await self.issue_repo.count_by_repo(repo.repo_id)
                except Exception as e:
                    logger.warning(
                        "get_project_landscape_issue_count_failed",
                        repo_id=repo.repo_id,
                        error=str(e),
                    )

            # Get languages from Qdrant
            languages: list[str] = []
            try:
                languages = await self.qdrant_client.get_unique_languages(repo.repo_id)
            except Exception as e:
                logger.warning(
                    "get_project_landscape_languages_failed",
                    repo_id=repo.repo_id,
                    error=str(e),
                )

            # Get owner for this repo
            owner = owners_map.get(repo.repo_id)

            # Add source citation for this repo
            sources.append(
                LandscapeSource(
                    source_type="repo",
                    source_id=repo.repo_id,
                    repo_id=repo.repo_id,
                    node_id=repo.node_id,
                    citation=f"Repository: {repo.name} on node {repo.node_id}",
                    included_at=datetime.utcnow(),
                )
            )

            repo_metadata.append(
                RepoMetadata(
                    repo_id=repo.repo_id,
                    node_id=repo.node_id,
                    file_count=file_count,
                    issue_count=issue_count,
                    last_indexed_at=None,
                    languages=languages,
                    owner=owner,
                )
            )

            total_files += file_count
            total_issues += issue_count

        # Build explicit relationships if requested
        relationships: list[RelatedRepo] | None = None
        relationship_count = 0
        if include_relationships and self.relationship_repo and len(repos) > 1:
            try:
                all_relationships = await self.relationship_repo.list_all()
                relationship_count = len(all_relationships)

                # Add source citations for relationships
                for rel in all_relationships:
                    sources.append(
                        LandscapeSource(
                            source_type="relationship",
                            source_id=rel.relationship_id,
                            repo_id=rel.source_repo_id,
                            node_id="",
                            citation=f"Relationship: {rel.source_repo_id} {rel.relationship_type.value} {rel.target_repo_id}",
                            included_at=datetime.utcnow(),
                        )
                    )

                # Convert to RelatedRepo format
                relationships = [
                    RelatedRepo(
                        repo_id=rel.target_repo_id,
                        node_id="",  # Would need to look up
                        relationship_type=rel.relationship_type.value,
                        overlap_score=rel.confidence,
                    )
                    for rel in all_relationships
                ]
            except Exception as e:
                logger.warning("get_project_landscape_get_relationships_failed", error=str(e))

        # Build landscape metadata with ownership and sources
        primary_owner: RepoOwner | None = None
        maintainers: list[RepoOwner] = []

        for owner in owners_map.values():
            if owner.role == "maintainer":
                maintainers.append(owner)
                if primary_owner is None:
                    primary_owner = owner

        landscape_metadata = LandscapeMetadata(
            owner=primary_owner,
            maintainers=maintainers,
            sources=sources,
            relationship_count=relationship_count,
            description="Project landscape with ownership and relationship metadata",
        )

        result = ProjectLandscape(
            total_repos=len(repos),
            total_files=total_files,
            total_issues=total_issues,
            repos=repo_metadata,
            relationships=relationships,
            landscape_metadata=landscape_metadata,
        )

        logger.info(
            "get_project_landscape_success",
            total_repos=len(repos),
            include_relationships=include_relationships,
            relationship_count=relationship_count,
            owner_count=len(owners_map),
        )

        return {
            "success": True,
            **result.model_dump(),
        }
