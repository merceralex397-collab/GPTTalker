"""Context bundle MCP tool handlers."""

from typing import Any

from pydantic import BaseModel, Field

from src.hub.services.bundle_service import BundleService


class BuildContextBundleParams(BaseModel):
    """Parameters for building a context bundle."""

    bundle_type: str = Field(
        ...,
        description="Type of bundle: task, review, or research",
        enum=["task", "review", "research"],
    )
    title: str = Field(..., description="Human-readable title for the bundle")
    description: str | None = Field(None, description="Optional description")
    repo_ids: list[str] = Field(
        ...,
        description="List of repository IDs to include in the bundle",
    )

    # Task bundle specific
    task_query: str | None = Field(
        None,
        description="For task bundles: natural language query describing the task",
    )

    # Review bundle specific
    changed_files: list[str] | None = Field(
        None,
        description="For review bundles: list of changed file paths",
    )
    related_issue_query: str | None = Field(
        None,
        description="For review bundles: query for related issues",
    )

    # Research bundle specific
    research_queries: list[str] | None = Field(
        None,
        description="For research bundles: list of research queries",
    )

    # Common options
    max_files: int = Field(
        20,
        description="Maximum number of files to include",
        ge=1,
        le=100,
    )
    max_issues: int = Field(
        10,
        description="Maximum number of issues to include",
        ge=1,
        le=100,
    )
    max_files_per_query: int = Field(
        10,
        description="For research: max files per query",
        ge=1,
        le=50,
    )
    max_issues_per_query: int = Field(
        5,
        description="For research: max issues per query",
        ge=1,
        le=50,
    )


async def build_context_bundle_handler(
    params: BuildContextBundleParams,
    bundle_service: BundleService,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Build a context bundle based on the specified parameters.

    This handler creates a task-oriented, review, or research bundle
    by aggregating relevant files and issues from the indexed context store.

    Args:
        params: Bundle construction parameters.
        bundle_service: BundleService instance.
        trace_id: Optional trace ID for request tracking.

    Returns:
        Dictionary containing the bundle and its items.
    """
    created_by = trace_id or "system"

    if params.bundle_type == "task":
        if not params.task_query:
            return {
                "success": False,
                "error": "task_query is required for task bundles",
            }

        return await bundle_service.build_task_bundle(
            title=params.title,
            description=params.description,
            task_query=params.task_query,
            repo_ids=params.repo_ids,
            max_files=params.max_files,
            max_issues=params.max_issues,
            created_by=created_by,
        )

    elif params.bundle_type == "review":
        if not params.changed_files:
            return {
                "success": False,
                "error": "changed_files is required for review bundles",
            }

        return await bundle_service.build_review_bundle(
            title=params.title,
            description=params.description,
            changed_files=params.changed_files,
            repo_ids=params.repo_ids,
            related_issue_query=params.related_issue_query,
            max_related_issues=params.max_issues,
            created_by=created_by,
        )

    elif params.bundle_type == "research":
        if not params.research_queries:
            return {
                "success": False,
                "error": "research_queries is required for research bundles",
            }

        return await bundle_service.build_research_bundle(
            title=params.title,
            description=params.description,
            research_queries=params.research_queries,
            repo_ids=params.repo_ids,
            max_files_per_query=params.max_files_per_query,
            max_issues_per_query=params.max_issues_per_query,
            created_by=created_by,
        )

    else:
        return {
            "success": False,
            "error": f"Unknown bundle type: {params.bundle_type}",
        }
