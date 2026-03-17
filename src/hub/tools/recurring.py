"""Recurring issue MCP tool handlers."""

from typing import Any

from pydantic import BaseModel, Field

from src.hub.services.aggregation_service import AggregationService


class ListRecurringIssuesParams(BaseModel):
    """Parameters for listing recurring issues."""

    aggregation_type: str = Field(
        "exact_title",
        description="Aggregation method: exact_title, semantic, or tag",
        enum=["exact_title", "semantic", "tag"],
    )
    repo_ids: list[str] | None = Field(
        None,
        description="Optional list of repository IDs to filter",
    )
    min_count: int = Field(
        2,
        description="Minimum issues required to form a recurring group",
        ge=2,
        le=100,
    )
    score_threshold: float = Field(
        0.85,
        description="For semantic aggregation: minimum similarity score",
        ge=0.0,
        le=1.0,
    )
    tag_key: str | None = Field(
        None,
        description="For tag aggregation: metadata key to group by",
    )
    status_filter: str | None = Field(
        None,
        description="Filter by issue status: open, resolved, wontfix",
        enum=["open", "resolved", "wontfix"],
    )


async def list_recurring_issues_handler(
    params: ListRecurringIssuesParams,
    aggregation_service: AggregationService,
) -> dict[str, Any]:
    """List recurring issues using the specified aggregation method.

    This handler identifies patterns across issues to help find:
    - Repeated bugs across releases
    - Common blockers or dependencies
    - Issues that may benefit from combined attention

    Args:
        params: Aggregation parameters.
        aggregation_service: AggregationService instance.

    Returns:
        Dictionary containing aggregated issue groups and summary.
    """
    return await aggregation_service.list_recurring_issues(
        aggregation_type=params.aggregation_type,
        repo_ids=params.repo_ids,
        min_count=params.min_count,
        score_threshold=params.score_threshold,
        tag_key=params.tag_key,
        status_filter=params.status_filter,
    )
