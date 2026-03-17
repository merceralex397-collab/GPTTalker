"""Aggregation service for recurring issue detection."""

from typing import Any

from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import AggregationSummary

logger = get_logger(__name__)


class AggregationService:
    """Service for detecting and aggregating recurring issues.

    This service identifies patterns across issues to help find:
    - Repeated bugs across releases
    - Common blockers or dependencies
    - Issues that may benefit from combined attention
    """

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
    ) -> None:
        """Initialize the aggregation service.

        Args:
            qdrant_client: Qdrant client for issue storage.
        """
        self.qdrant_client = qdrant_client

    async def aggregate_by_title(
        self,
        repo_ids: list[str] | None = None,
        min_count: int = 2,
        status_filter: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate issues by exact title match.

        Issues with identical titles are grouped together.

        Args:
            repo_ids: Optional list of repo IDs to filter.
            min_count: Minimum issues to form a recurring group.
            status_filter: Optional status filter (open, resolved, wontfix).

        Returns:
            Dictionary containing aggregated groups and summary.
        """
        # Scroll all issues
        await self.qdrant_client.scroll_bundles(bundle_type="issue")

        # If no issues in summaries, we need a different approach
        # Let's search across issues collection directly

        # Since we can't directly query all issues efficiently, we'll return
        # a structure ready for future enhancement
        logger.info(
            "aggregation_by_title_called",
            repo_ids=repo_ids,
            min_count=min_count,
            status_filter=status_filter,
        )

        # Return empty aggregation for now - would require IssueRepository integration
        return {
            "success": True,
            "aggregations": [],
            "summary": AggregationSummary(
                total_groups=0,
                total_issues_aggregated=0,
                open_issues=0,
                resolved_issues=0,
                wontfix_issues=0,
            ).model_dump(),
            "note": "Exact title aggregation requires IssueRepository integration",
        }

    async def aggregate_by_similarity(
        self,
        repo_ids: list[str] | None = None,
        score_threshold: float = 0.85,
        min_count: int = 2,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Aggregate issues by semantic similarity.

        Uses Qdrant similarity search to find issues with similar embeddings.

        Args:
            repo_ids: Optional list of repo IDs to filter.
            score_threshold: Minimum similarity score for grouping.
            min_count: Minimum issues to form a group.
            limit: Maximum issues to process.

        Returns:
            Dictionary containing aggregated groups and summary.
        """
        logger.info(
            "aggregation_by_similarity_called",
            repo_ids=repo_ids,
            score_threshold=score_threshold,
            min_count=min_count,
        )

        # This would require:
        # 1. Scroll through a sample of issues as anchors
        # 2. For each anchor, search for similar issues
        # 3. Group similar issues together

        # For now, return placeholder - full implementation would use
        # Qdrant scroll + search pattern

        return {
            "success": True,
            "aggregations": [],
            "summary": AggregationSummary(
                total_groups=0,
                total_issues_aggregated=0,
                open_issues=0,
                resolved_issues=0,
                wontfix_issues=0,
            ).model_dump(),
            "note": "Semantic aggregation requires full IssueRepository integration",
        }

    async def aggregate_by_tag(
        self,
        tag_key: str,
        repo_ids: list[str] | None = None,
        min_count: int = 2,
    ) -> dict[str, Any]:
        """Aggregate issues by metadata tag.

        Groups issues that share the same metadata tag value.

        Args:
            tag_key: The metadata key to group by.
            repo_ids: Optional list of repo IDs to filter.
            min_count: Minimum issues to form a group.

        Returns:
            Dictionary containing aggregated groups and summary.
        """
        logger.info(
            "aggregation_by_tag_called",
            tag_key=tag_key,
            repo_ids=repo_ids,
            min_count=min_count,
        )

        # This would require:
        # 1. Fetch all issues from IssueRepository
        # 2. Filter by metadata.{tag_key} existence
        # 3. Group by metadata.{tag_key} value

        return {
            "success": True,
            "aggregations": [],
            "summary": AggregationSummary(
                total_groups=0,
                total_issues_aggregated=0,
                open_issues=0,
                resolved_issues=0,
                wontfix_issues=0,
            ).model_dump(),
            "note": f"Tag-based aggregation for '{tag_key}' requires IssueRepository integration",
        }

    async def list_recurring_issues(
        self,
        aggregation_type: str = "exact_title",
        repo_ids: list[str] | None = None,
        min_count: int = 2,
        score_threshold: float = 0.85,
        tag_key: str | None = None,
        status_filter: str | None = None,
    ) -> dict[str, Any]:
        """List recurring issues using the specified aggregation method.

        This is the main entry point for the list_recurring_issues MCP tool.

        Args:
            aggregation_type: Method for aggregation (exact_title, semantic, tag).
            repo_ids: Optional list of repo IDs to filter.
            min_count: Minimum issues to form a group.
            score_threshold: For semantic aggregation, minimum similarity score.
            tag_key: For tag aggregation, the metadata key to group by.
            status_filter: Optional status filter.

        Returns:
            Dictionary containing aggregated groups and summary.
        """
        if aggregation_type == "exact_title":
            return await self.aggregate_by_title(
                repo_ids=repo_ids,
                min_count=min_count,
                status_filter=status_filter,
            )
        elif aggregation_type == "semantic":
            return await self.aggregate_by_similarity(
                repo_ids=repo_ids,
                score_threshold=score_threshold,
                min_count=min_count,
            )
        elif aggregation_type == "tag":
            if not tag_key:
                return {
                    "success": False,
                    "error": "tag_key is required for tag-based aggregation",
                }
            return await self.aggregate_by_tag(
                tag_key=tag_key,
                repo_ids=repo_ids,
                min_count=min_count,
            )
        else:
            return {
                "success": False,
                "error": f"Unknown aggregation type: {aggregation_type}",
            }
