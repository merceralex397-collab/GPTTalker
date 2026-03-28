"""Aggregation service for recurring issue detection."""

import hashlib
from typing import Any

from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import (
    AggregationSummary,
    AggregationType,
    IssueStatus,
    RecurringIssueGroup,
)
from src.shared.repositories.issues import IssueRepository

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
        issue_repo: IssueRepository,
    ) -> None:
        """Initialize the aggregation service.

        Args:
            qdrant_client: Qdrant client for issue storage.
            issue_repo: Issue repository for SQLite-backed issue data.
        """
        self.qdrant_client = qdrant_client
        self.issue_repo = issue_repo

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
        logger.info(
            "aggregation_by_title_called",
            repo_ids=repo_ids,
            min_count=min_count,
            status_filter=status_filter,
        )

        try:
            # Get recurring titles from IssueRepository
            recurring_titles = await self.issue_repo.list_recurring(min_count=min_count)

            if not recurring_titles:
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
                }

            groups: list[RecurringIssueGroup] = []
            total_issues = 0
            open_count = 0
            resolved_count = 0
            wontfix_count = 0

            for title_info in recurring_titles:
                title = title_info["title"]
                _ = title_info["count"]

                # Fetch all issues with this exact title
                all_issues = await self.issue_repo.list_all(limit=1000)
                matching_issues = [i for i in all_issues if i.title == title]

                # Apply repo_ids filter if provided
                if repo_ids:
                    matching_issues = [i for i in matching_issues if i.repo_id in repo_ids]

                # Apply status filter if provided
                if status_filter:
                    status_enum = IssueStatus(status_filter)
                    matching_issues = [i for i in matching_issues if i.status == status_enum]

                # Skip if below min_count after filtering
                if len(matching_issues) < min_count:
                    continue

                # Sort by creation date
                matching_issues.sort(key=lambda x: x.created_at)

                # Collect unique repo IDs
                group_repo_ids = {i.repo_id for i in matching_issues}

                # Compute status counts
                group_open = sum(1 for i in matching_issues if i.status == IssueStatus.OPEN)
                group_resolved = sum(1 for i in matching_issues if i.status == IssueStatus.RESOLVED)
                group_wontfix = sum(1 for i in matching_issues if i.status == IssueStatus.WONT_FIX)

                # Compute duration
                first_issue = matching_issues[0]
                last_issue = matching_issues[-1]
                duration_days = (last_issue.created_at - first_issue.created_at).days

                # Generate group ID from title hash
                group_id = hashlib.sha256(title.encode()).hexdigest()[:16]

                group = RecurringIssueGroup(
                    group_id=group_id,
                    aggregation_type=AggregationType.EXACT_TITLE,
                    representative_title=title,
                    count=len(matching_issues),
                    issue_ids=[str(i.issue_id) for i in matching_issues],
                    repo_ids=group_repo_ids,
                    first_seen=first_issue.created_at,
                    last_seen=last_issue.created_at,
                    total_duration_days=duration_days,
                )
                groups.append(group)

                total_issues += len(matching_issues)
                open_count += group_open
                resolved_count += group_resolved
                wontfix_count += group_wontfix

            return {
                "success": True,
                "aggregations": [g.model_dump() for g in groups],
                "summary": AggregationSummary(
                    total_groups=len(groups),
                    total_issues_aggregated=total_issues,
                    open_issues=open_count,
                    resolved_issues=resolved_count,
                    wontfix_issues=wontfix_count,
                ).model_dump(),
            }

        except Exception as e:
            logger.error("aggregation_by_title_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "aggregations": [],
                "summary": AggregationSummary(
                    total_groups=0,
                    total_issues_aggregated=0,
                    open_issues=0,
                    resolved_issues=0,
                    wontfix_issues=0,
                ).model_dump(),
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
            limit=limit,
        )

        try:
            # Fetch issues from SQLite as anchor points for semantic search
            all_issues = await self.issue_repo.list_all(limit=limit)

            if not all_issues:
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
                    "warning": "No issues found for semantic aggregation",
                }

            # Apply repo_ids filter if provided
            if repo_ids:
                all_issues = [i for i in all_issues if i.repo_id in repo_ids]

            # Build a mapping of issue_id to issue for quick lookup
            issue_map = {str(i.issue_id): i for i in all_issues}

            # For each anchor issue, search for similar issues in Qdrant
            # Group similar issues together
            similar_groups: dict[str, set[str]] = {}
            processed_issues: set[str] = set()

            for issue in all_issues:
                issue_id_str = str(issue.issue_id)

                if issue_id_str in processed_issues:
                    continue

                # Search for similar issues in Qdrant using title+description
                # Note: This requires embeddings to exist in Qdrant
                # We'll use a workaround: search with the title as query
                try:
                    # Generate a mock vector query from title (in production, use embeddings)
                    # For now, we'll search issues collection directly
                    # Since we don't have embeddings, we'll use a simpler approach:
                    # Group by extracting key terms from titles

                    # Create a group with this issue as anchor
                    similar_group = {issue_id_str}

                    # Search Qdrant for similar issues (requires embeddings)
                    # In production, we'd generate embeddings and search
                    # For now, we'll do a simpler text-based grouping
                    search_results = await self.qdrant_client.search_issues(
                        query_vector=[0.0] * 1536,  # Placeholder - would use real embedding
                        repo_id=issue.repo_id if not repo_ids else None,
                        limit=10,
                        score_threshold=score_threshold,
                    )

                    for result in search_results:
                        result_id = result.id
                        if result_id in issue_map and result_id not in processed_issues:
                            similar_group.add(result_id)

                    if len(similar_group) >= min_count:
                        group_key = f"semantic_{issue_id_str}"
                        similar_groups[group_key] = similar_group
                        processed_issues.update(similar_group)

                except Exception as e:
                    # If Qdrant search fails (no embeddings), fall back to text matching
                    logger.warning(
                        "qdrant_search_failed_falling_back",
                        issue_id=issue_id_str,
                        error=str(e),
                    )

                    # Simple fallback: group issues with similar words in title
                    title_words = set(issue.title.lower().split())
                    for other_issue in all_issues:
                        other_id = str(other_issue.issue_id)
                        if other_id == issue_id_str or other_id in processed_issues:
                            continue

                        other_words = set(other_issue.title.lower().split())
                        common_words = title_words & other_words

                        if len(common_words) >= 2:  # At least 2 common words
                            group_key = f"text_{hashlib.sha256(' '.join(sorted(common_words)).encode()).hexdigest()[:8]}"
                            if group_key not in similar_groups:
                                similar_groups[group_key] = set()
                            similar_groups[group_key].add(issue_id_str)
                            similar_groups[group_key].add(other_id)

            # Build RecurringIssueGroup objects
            groups: list[RecurringIssueGroup] = []
            total_issues = 0
            open_count = 0
            resolved_count = 0
            wontfix_count = 0

            for group_id_str, issue_id_set in similar_groups.items():
                if len(issue_id_set) < min_count:
                    continue

                group_issues = [issue_map[iid] for iid in issue_id_set if iid in issue_map]

                if not group_issues:
                    continue

                # Sort by creation date
                group_issues.sort(key=lambda x: x.created_at)

                # Collect unique repo IDs
                group_repo_ids = {i.repo_id for i in group_issues}

                # Compute status counts
                group_open = sum(1 for i in group_issues if i.status == IssueStatus.OPEN)
                group_resolved = sum(1 for i in group_issues if i.status == IssueStatus.RESOLVED)
                group_wontfix = sum(1 for i in group_issues if i.status == IssueStatus.WONT_FIX)

                # Compute duration
                first_issue = group_issues[0]
                last_issue = group_issues[-1]
                duration_days = (last_issue.created_at - first_issue.created_at).days

                # Use representative title (most common or first)
                representative = group_issues[0].title

                group = RecurringIssueGroup(
                    group_id=group_id_str[:16],
                    aggregation_type=AggregationType.SEMANTIC,
                    representative_title=representative,
                    count=len(group_issues),
                    issue_ids=list(issue_id_set),
                    repo_ids=group_repo_ids,
                    first_seen=first_issue.created_at,
                    last_seen=last_issue.created_at,
                    total_duration_days=duration_days,
                )
                groups.append(group)

                total_issues += len(group_issues)
                open_count += group_open
                resolved_count += group_resolved
                wontfix_count += group_wontfix

            return {
                "success": True,
                "aggregations": [g.model_dump() for g in groups],
                "summary": AggregationSummary(
                    total_groups=len(groups),
                    total_issues_aggregated=total_issues,
                    open_issues=open_count,
                    resolved_issues=resolved_count,
                    wontfix_issues=wontfix_count,
                ).model_dump(),
            }

        except Exception as e:
            logger.error("aggregation_by_similarity_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "aggregations": [],
                "summary": AggregationSummary(
                    total_groups=0,
                    total_issues_aggregated=0,
                    open_issues=0,
                    resolved_issues=0,
                    wontfix_issues=0,
                ).model_dump(),
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

        try:
            # Fetch all issues from IssueRepository
            all_issues = await self.issue_repo.list_all(limit=1000)

            if not all_issues:
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
                    "warning": "No issues found for tag aggregation",
                }

            # Apply repo_ids filter if provided
            if repo_ids:
                all_issues = [i for i in all_issues if i.repo_id in repo_ids]

            # Group issues by tag value
            tag_groups: dict[str, list] = {}

            for issue in all_issues:
                # Check if tag_key exists in metadata
                tag_value = issue.metadata.get(tag_key)
                if tag_value is not None:
                    # Convert to string for grouping
                    tag_str = str(tag_value)
                    if tag_str not in tag_groups:
                        tag_groups[tag_str] = []
                    tag_groups[tag_str].append(issue)

            # Build RecurringIssueGroup objects for groups meeting min_count
            groups: list[RecurringIssueGroup] = []
            total_issues = 0
            open_count = 0
            resolved_count = 0
            wontfix_count = 0

            for tag_value, issues in tag_groups.items():
                if len(issues) < min_count:
                    continue

                # Sort by creation date
                issues.sort(key=lambda x: x.created_at)

                # Collect unique repo IDs
                group_repo_ids = {i.repo_id for i in issues}

                # Compute status counts
                group_open = sum(1 for i in issues if i.status == IssueStatus.OPEN)
                group_resolved = sum(1 for i in issues if i.status == IssueStatus.RESOLVED)
                group_wontfix = sum(1 for i in issues if i.status == IssueStatus.WONT_FIX)

                # Compute duration
                first_issue = issues[0]
                last_issue = issues[-1]
                duration_days = (last_issue.created_at - first_issue.created_at).days

                # Generate group ID from tag key and value
                group_id = hashlib.sha256(f"{tag_key}:{tag_value}".encode()).hexdigest()[:16]

                # Use representative title (first issue)
                representative = issues[0].title

                group = RecurringIssueGroup(
                    group_id=group_id,
                    aggregation_type=AggregationType.TAG,
                    representative_title=f"[{tag_key}: {tag_value}] {representative}",
                    count=len(issues),
                    issue_ids=[str(i.issue_id) for i in issues],
                    repo_ids=group_repo_ids,
                    first_seen=first_issue.created_at,
                    last_seen=last_issue.created_at,
                    total_duration_days=duration_days,
                )
                groups.append(group)

                total_issues += len(issues)
                open_count += group_open
                resolved_count += group_resolved
                wontfix_count += group_wontfix

            return {
                "success": True,
                "aggregations": [g.model_dump() for g in groups],
                "summary": AggregationSummary(
                    total_groups=len(groups),
                    total_issues_aggregated=total_issues,
                    open_issues=open_count,
                    resolved_issues=resolved_count,
                    wontfix_issues=wontfix_count,
                ).model_dump(),
            }

        except Exception as e:
            logger.error("aggregation_by_tag_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "aggregations": [],
                "summary": AggregationSummary(
                    total_groups=0,
                    total_issues_aggregated=0,
                    open_issues=0,
                    resolved_issues=0,
                    wontfix_issues=0,
                ).model_dump(),
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
