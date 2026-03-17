"""Bundle service for assembling context bundles."""

import hashlib
import time
from datetime import datetime
from typing import Any

from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import (
    BundleSource,
    BundleType,
    ContextBundlePayload,
    FileIndexPayload,
    IssueIndexPayload,
)

logger = get_logger(__name__)


class BundleService:
    """Service for assembling and managing context bundles.

    This service handles the creation of task-oriented, review, and research
    bundles by aggregating relevant files, issues, and metadata from the
    indexed context store.
    """

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
        embedding_client: EmbeddingServiceClient,
        embedding_service_id: str,
    ) -> None:
        """Initialize the bundle service.

        Args:
            qdrant_client: Qdrant client for context storage.
            embedding_client: Client for generating embeddings.
            embedding_service_id: Service ID for the embedding service.
        """
        self.qdrant_client = qdrant_client
        self.embedding_client = embedding_client
        self.embedding_service_id = embedding_service_id

    def _generate_bundle_id(self, title: str, created_at: datetime) -> str:
        """Generate a unique bundle ID.

        Args:
            title: Bundle title.
            created_at: Creation timestamp.

        Returns:
            Unique bundle identifier.
        """
        key = f"{title}:{created_at.isoformat()}"
        return f"bundle_{hashlib.sha256(key.encode()).hexdigest()[:16]}"

    async def build_task_bundle(
        self,
        title: str,
        description: str | None,
        task_query: str,
        repo_ids: list[str],
        max_files: int = 20,
        max_issues: int = 10,
        created_by: str = "system",
    ) -> dict[str, Any]:
        """Build a task-oriented context bundle.

        Args:
            title: Bundle title.
            description: Optional bundle description.
            task_query: Natural language query describing the task.
            repo_ids: List of repo IDs to include in the bundle.
            max_files: Maximum number of files to include.
            max_issues: Maximum number of issues to include.
            created_by: Trace ID of the creator.

        Returns:
            Dictionary containing the bundle and its items.
        """
        start_time = time.perf_counter()
        created_at = datetime.utcnow()
        bundle_id = self._generate_bundle_id(title, created_at)

        # Generate query embedding
        query_embedding = await self.embedding_client.embed(
            service_id=self.embedding_service_id,
            text=task_query,
        )

        # Search for relevant files
        file_results = await self.qdrant_client.search_files(
            query_vector=query_embedding,
            repo_ids=repo_ids,
            limit=max_files,
            score_threshold=0.5,
        )

        # Search for relevant issues
        issue_results = await self.qdrant_client.search_issues(
            query_vector=query_embedding,
            limit=max_issues,
            score_threshold=0.5,
        )

        # Build provenance sources
        sources: list[BundleSource] = []
        file_ids: list[str] = []
        issue_ids: list[str] = []

        for record in file_results:
            payload = FileIndexPayload(**record.payload)
            file_ids.append(payload.file_id)
            sources.append(
                BundleSource(
                    source_type="file",
                    source_id=payload.file_id,
                    repo_id=payload.repo_id,
                    node_id=payload.node_id,
                    included_at=created_at,
                    relevance_score=float(record.score) if record.score else None,
                    reason=f"semantic match for '{task_query}'",
                )
            )

        for record in issue_results:
            payload = IssueIndexPayload(**record.payload)
            issue_ids.append(payload.issue_id)
            sources.append(
                BundleSource(
                    source_type="issue",
                    source_id=payload.issue_id,
                    repo_id=payload.repo_id,
                    node_id="",
                    included_at=created_at,
                    relevance_score=float(record.score) if record.score else None,
                    reason=f"semantic match for '{task_query}'",
                )
            )

        # Create bundle payload
        bundle_payload = ContextBundlePayload(
            bundle_id=bundle_id,
            bundle_type=BundleType.TASK,
            title=title,
            description=description,
            created_at=created_at,
            created_by=created_by,
            repo_ids=repo_ids,
            file_ids=file_ids,
            issue_ids=issue_ids,
            sources=sources,
            task_type=task_query,
            generation_method="semantic_similarity",
        )

        # Generate bundle embedding and store
        bundle_embedding = await self.embedding_client.embed(
            service_id=self.embedding_service_id,
            text=f"{title} {description or ''} {task_query}",
        )

        await self.qdrant_client.upsert_bundle(
            bundle_id=bundle_id,
            vector=bundle_embedding,
            payload=bundle_payload,
        )

        # Build response with file details
        files = []
        for record in file_results:
            payload = FileIndexPayload(**record.payload)
            files.append(
                {
                    "file_id": payload.file_id,
                    "repo_id": payload.repo_id,
                    "path": payload.relative_path,
                    "content_preview": payload.content_preview,
                    "relevance_score": float(record.score) if record.score else None,
                    "included_reason": f"semantic match for '{task_query}'",
                }
            )

        issues = []
        for record in issue_results:
            payload = IssueIndexPayload(**record.payload)
            issues.append(
                {
                    "issue_id": payload.issue_id,
                    "repo_id": payload.repo_id,
                    "title": payload.title,
                    "status": payload.status,
                    "relevance_score": float(record.score) if record.score else None,
                    "included_reason": f"semantic match for '{task_query}'",
                }
            )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "success": True,
            "bundle_id": bundle_id,
            "bundle_type": "task",
            "title": title,
            "created_at": created_at.isoformat() + "Z",
            "files": files,
            "issues": issues,
            "provenance": {
                "total_sources": len(sources),
                "repos_included": list(set(repo_ids)),
                "created_by": created_by,
                "generation_method": "semantic_similarity",
            },
            "latency_ms": latency_ms,
        }

    async def build_review_bundle(
        self,
        title: str,
        description: str | None,
        changed_files: list[str],
        repo_ids: list[str],
        related_issue_query: str | None = None,
        max_related_issues: int = 5,
        created_by: str = "system",
    ) -> dict[str, Any]:
        """Build a review-oriented context bundle.

        Args:
            title: Bundle title.
            description: Optional bundle description.
            changed_files: List of changed file paths.
            repo_ids: List of repo IDs to include.
            related_issue_query: Optional query for related issues.
            max_related_issues: Maximum related issues to include.
            created_by: Trace ID of the creator.

        Returns:
            Dictionary containing the bundle and its items.
        """
        start_time = time.perf_counter()
        created_at = datetime.utcnow()
        bundle_id = self._generate_bundle_id(title, created_at)

        # Get file details from Qdrant
        files = []
        file_ids = []
        node_ids: set[str] = set()
        sources: list[BundleSource] = []

        for file_path in changed_files:
            # Find file by path - scroll through repo files
            for repo_id in repo_ids:
                records = await self.qdrant_client.scroll_files(repo_id=repo_id, limit=1000)
                for record in records:
                    payload = FileIndexPayload(**record.payload)
                    if payload.relative_path == file_path or payload.path.endswith(file_path):
                        file_ids.append(payload.file_id)
                        node_ids.add(payload.node_id)
                        sources.append(
                            BundleSource(
                                source_type="file",
                                source_id=payload.file_id,
                                repo_id=payload.repo_id,
                                node_id=payload.node_id,
                                included_at=created_at,
                                relevance_score=1.0,
                                reason="changed file in review",
                            )
                        )
                        files.append(
                            {
                                "file_id": payload.file_id,
                                "repo_id": payload.repo_id,
                                "path": payload.relative_path,
                                "content_preview": payload.content_preview,
                                "relevance_score": 1.0,
                                "included_reason": "changed file in review",
                            }
                        )
                        break

        # Search for related issues if query provided
        issues = []
        issue_ids = []
        if related_issue_query:
            query_embedding = await self.embedding_client.embed(
                service_id=self.embedding_service_id,
                text=related_issue_query,
            )
            issue_results = await self.qdrant_client.search_issues(
                query_vector=query_embedding,
                repo_id=None,  # Search across all repos
                limit=max_related_issues,
                score_threshold=0.5,
            )

            for record in issue_results:
                payload = IssueIndexPayload(**record.payload)
                issue_ids.append(payload.issue_id)
                sources.append(
                    BundleSource(
                        source_type="issue",
                        source_id=payload.issue_id,
                        repo_id=payload.repo_id,
                        node_id="",
                        included_at=created_at,
                        relevance_score=float(record.score) if record.score else None,
                        reason=f"related to review: {related_issue_query}",
                    )
                )
                issues.append(
                    {
                        "issue_id": payload.issue_id,
                        "repo_id": payload.repo_id,
                        "title": payload.title,
                        "status": payload.status,
                        "relevance_score": float(record.score) if record.score else None,
                        "included_reason": f"related to review: {related_issue_query}",
                    }
                )

        # Create bundle payload
        bundle_payload = ContextBundlePayload(
            bundle_id=bundle_id,
            bundle_type=BundleType.REVIEW,
            title=title,
            description=description,
            created_at=created_at,
            created_by=created_by,
            repo_ids=repo_ids,
            file_ids=file_ids,
            issue_ids=issue_ids,
            sources=sources,
            generation_method="manual",
        )

        # Generate bundle embedding and store
        bundle_embedding = await self.embedding_client.embed(
            service_id=self.embedding_service_id,
            text=f"{title} {description or ''} review",
        )

        await self.qdrant_client.upsert_bundle(
            bundle_id=bundle_id,
            vector=bundle_embedding,
            payload=bundle_payload,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "success": True,
            "bundle_id": bundle_id,
            "bundle_type": "review",
            "title": title,
            "created_at": created_at.isoformat() + "Z",
            "files": files,
            "issues": issues,
            "provenance": {
                "total_sources": len(sources),
                "repos_included": list(set(repo_ids)),
                "created_by": created_by,
                "generation_method": "manual",
            },
            "latency_ms": latency_ms,
        }

    async def build_research_bundle(
        self,
        title: str,
        description: str | None,
        research_queries: list[str],
        repo_ids: list[str],
        max_files_per_query: int = 10,
        max_issues_per_query: int = 5,
        created_by: str = "system",
    ) -> dict[str, Any]:
        """Build a research-oriented context bundle.

        Args:
            title: Bundle title.
            description: Optional bundle description.
            research_queries: List of queries for research exploration.
            repo_ids: List of repo IDs to include.
            max_files_per_query: Maximum files per query.
            max_issues_per_query: Maximum issues per query.
            created_by: Trace ID of the creator.

        Returns:
            Dictionary containing the bundle and its items.
        """
        start_time = time.perf_counter()
        created_at = datetime.utcnow()
        bundle_id = self._generate_bundle_id(title, created_at)

        all_files: list[dict[str, Any]] = []
        all_issues: list[dict[str, Any]] = []
        file_ids: list[str] = []
        issue_ids: list[str] = []
        sources: list[BundleSource] = []

        # Process each research query
        for query in research_queries:
            query_embedding = await self.embedding_client.embed(
                service_id=self.embedding_service_id,
                text=query,
            )

            # Search files
            file_results = await self.qdrant_client.search_files(
                query_vector=query_embedding,
                repo_ids=repo_ids,
                limit=max_files_per_query,
                score_threshold=0.5,
            )

            for record in file_results:
                payload = FileIndexPayload(**record.payload)
                if payload.file_id not in file_ids:
                    file_ids.append(payload.file_id)
                    all_files.append(
                        {
                            "file_id": payload.file_id,
                            "repo_id": payload.repo_id,
                            "path": payload.relative_path,
                            "content_preview": payload.content_preview,
                            "relevance_score": float(record.score) if record.score else None,
                            "included_reason": f"research query: {query}",
                        }
                    )
                    sources.append(
                        BundleSource(
                            source_type="file",
                            source_id=payload.file_id,
                            repo_id=payload.repo_id,
                            node_id=payload.node_id,
                            included_at=created_at,
                            relevance_score=float(record.score) if record.score else None,
                            reason=f"research query: {query}",
                        )
                    )

            # Search issues
            issue_results = await self.qdrant_client.search_issues(
                query_vector=query_embedding,
                limit=max_issues_per_query,
                score_threshold=0.5,
            )

            for record in issue_results:
                payload = IssueIndexPayload(**record.payload)
                if payload.issue_id not in issue_ids:
                    issue_ids.append(payload.issue_id)
                    all_issues.append(
                        {
                            "issue_id": payload.issue_id,
                            "repo_id": payload.repo_id,
                            "title": payload.title,
                            "status": payload.status,
                            "relevance_score": float(record.score) if record.score else None,
                            "included_reason": f"research query: {query}",
                        }
                    )
                    sources.append(
                        BundleSource(
                            source_type="issue",
                            source_id=payload.issue_id,
                            repo_id=payload.repo_id,
                            node_id="",
                            included_at=created_at,
                            relevance_score=float(record.score) if record.score else None,
                            reason=f"research query: {query}",
                        )
                    )

        # Create bundle payload
        bundle_payload = ContextBundlePayload(
            bundle_id=bundle_id,
            bundle_type=BundleType.RESEARCH,
            title=title,
            description=description,
            created_at=created_at,
            created_by=created_by,
            repo_ids=repo_ids,
            file_ids=file_ids,
            issue_ids=issue_ids,
            sources=sources,
            generation_method="semantic_similarity",
        )

        # Generate bundle embedding and store
        combined_text = f"{title} {' '.join(research_queries)}"
        bundle_embedding = await self.embedding_client.embed(
            service_id=self.embedding_service_id,
            text=combined_text,
        )

        await self.qdrant_client.upsert_bundle(
            bundle_id=bundle_id,
            vector=bundle_embedding,
            payload=bundle_payload,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "success": True,
            "bundle_id": bundle_id,
            "bundle_type": "research",
            "title": title,
            "created_at": created_at.isoformat() + "Z",
            "files": all_files,
            "issues": all_issues,
            "provenance": {
                "total_sources": len(sources),
                "repos_included": list(set(repo_ids)),
                "created_by": created_by,
                "generation_method": "semantic_similarity",
            },
            "latency_ms": latency_ms,
        }

    async def get_bundle(self, bundle_id: str) -> dict[str, Any] | None:
        """Retrieve a bundle by ID.

        Args:
            bundle_id: Bundle identifier.

        Returns:
            Bundle data or None if not found.
        """
        record = await self.qdrant_client.get_bundle(bundle_id)
        if not record:
            return None

        return {
            "bundle_id": record.id,
            "payload": record.payload,
        }
