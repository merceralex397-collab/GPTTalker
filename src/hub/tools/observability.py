"""Observability tools for task history, doc history, and issue timelines."""

import time
from typing import TYPE_CHECKING, Any

from src.shared.logging import get_logger

# Import type hints for forward references only
if TYPE_CHECKING:
    from src.shared.repositories.tasks import TaskRepository
    from src.shared.repositories.generated_docs import GeneratedDocsRepository
    from src.shared.repositories.issues import IssueRepository

logger = get_logger(__name__)


async def get_task_details_handler(
    task_id: str | None = None,
    trace_id: str | None = None,
    task_repo: "TaskRepository | None" = None,
) -> dict[str, Any]:
    """Get detailed information about a specific task.

    This tool provides access to task history records for debugging
    and audit purposes. Either task_id or trace_id must be provided.

    Args:
        task_id: Specific task ID to look up.
        trace_id: Trace ID to search for related tasks.
        task_repo: TaskRepository injected by the router.

    Returns:
        Dictionary with task details or list of matching tasks.
    """
    if task_repo is None:
        return {"error": "TaskRepository not available"}

    if task_id is None and trace_id is None:
        return {"error": "Either task_id or trace_id must be provided"}

    return await get_task_details_impl(task_repo, task_id, trace_id)


async def get_task_details_impl(
    task_repo: "TaskRepository",
    task_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Internal implementation for get_task_details.

    Args:
        task_repo: TaskRepository instance.
        task_id: Specific task ID to look up.
        trace_id: Trace ID to search for related tasks.

    Returns:
        Task details response.
    """
    start = int(time.time() * 1000)

    if task_id:
        task = await task_repo.get(task_id)
        duration = int(time.time() * 1000) - start

        if task is None:
            logger.info("get_task_details_not_found", task_id=task_id)
            return {"error": f"Task not found: {task_id}"}

        logger.info("get_task_details_executed", task_id=task_id, duration_ms=duration)

        return {
            "task": {
                "task_id": str(task.task_id),
                "trace_id": task.trace_id,
                "tool_name": task.tool_name,
                "caller": task.caller,
                "target_node": task.target_node,
                "target_repo": task.target_repo,
                "outcome": task.outcome.value,
                "duration_ms": task.duration_ms,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "created_at": task.created_at.isoformat(),
                "error": task.error,
                "metadata": task.metadata,
            }
        }
    else:
        # trace_id search
        tasks = await task_repo.get_by_trace(trace_id)
        duration = int(time.time() * 1000) - start

        logger.info(
            "get_task_details_by_trace_executed",
            trace_id=trace_id,
            count=len(tasks),
            duration_ms=duration,
        )

        tasks_data = []
        for task in tasks:
            tasks_data.append(
                {
                    "task_id": str(task.task_id),
                    "trace_id": task.trace_id,
                    "tool_name": task.tool_name,
                    "caller": task.caller,
                    "target_node": task.target_node,
                    "target_repo": task.target_repo,
                    "outcome": task.outcome.value,
                    "duration_ms": task.duration_ms,
                    "created_at": task.created_at.isoformat(),
                    "error": task.error,
                }
            )

        return {
            "tasks": tasks_data,
            "total": len(tasks_data),
            "trace_id": trace_id,
        }


async def list_generated_docs_handler(
    limit: int = 50,
    tool_name: str | None = None,
    caller: str | None = None,
    doc_repo: "GeneratedDocsRepository | None" = None,
) -> dict[str, Any]:
    """List generated document history.

    This tool provides access to the history of generated documents
    for audit and tracking purposes.

    Args:
        limit: Maximum number of records to return (default 50).
        tool_name: Optional filter by tool name.
        caller: Optional filter by caller identifier.
        doc_repo: GeneratedDocsRepository injected by the router.

    Returns:
        Dictionary with list of generated documents.
    """
    if doc_repo is None:
        return {"error": "GeneratedDocsRepository not available"}

    return await list_generated_docs_impl(doc_repo, limit, tool_name, caller)


async def list_generated_docs_impl(
    doc_repo: "GeneratedDocsRepository",
    limit: int = 50,
    tool_name: str | None = None,
    caller: str | None = None,
) -> dict[str, Any]:
    """Internal implementation for list_generated_docs.

    Args:
        doc_repo: GeneratedDocsRepository instance.
        limit: Maximum number of records to return.
        tool_name: Optional filter by tool name.
        caller: Optional filter by caller identifier.

    Returns:
        Generated docs list response.
    """
    start = int(time.time() * 1000)

    # Apply filters
    if tool_name:
        docs = await doc_repo.list_by_tool(tool_name, limit)
    elif caller:
        docs = await doc_repo.list_by_caller(caller, limit)
    else:
        docs = await doc_repo.list_all(limit)

    duration = int(time.time() * 1000) - start

    docs_data = []
    for doc in docs:
        docs_data.append(
            {
                "doc_id": str(doc.doc_id),
                "trace_id": doc.trace_id,
                "tool_name": doc.tool_name,
                "caller": doc.caller,
                "target_path": doc.target_path,
                "content_hash": doc.content_hash,
                "size_bytes": doc.size_bytes,
                "created_at": doc.created_at.isoformat(),
                "metadata": doc.metadata,
            }
        )

    logger.info(
        "list_generated_docs_executed",
        total=len(docs_data),
        tool_name=tool_name,
        caller=caller,
        duration_ms=duration,
    )

    return {
        "documents": docs_data,
        "total": len(docs_data),
        "filters": {
            "tool_name": tool_name,
            "caller": caller,
        },
    }


async def list_known_issues_handler(
    repo_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    issue_repo: "IssueRepository | None" = None,
) -> dict[str, Any]:
    """List known issues with optional filtering.

    This tool provides access to issue records for audit and tracking purposes.
    Can filter by repo_id, status, or both.

    Args:
        repo_id: Optional repository ID to filter issues.
        status: Optional issue status to filter by (open, in_progress, resolved, wontfix).
        limit: Maximum number of issues to return (default 50).
        issue_repo: IssueRepository injected by the router.

    Returns:
        Dictionary with list of issues.
    """
    if issue_repo is None:
        return {"error": "IssueRepository not available"}

    return await list_known_issues_impl(issue_repo, repo_id, status, limit)


async def list_known_issues_impl(
    issue_repo: "IssueRepository",
    repo_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Internal implementation for list_known_issues.

    Args:
        issue_repo: IssueRepository instance.
        repo_id: Optional repository ID to filter issues.
        status: Optional issue status to filter by.
        limit: Maximum number of issues to return.

    Returns:
        Issues list response.
    """
    from src.shared.models import IssueStatus

    start = int(time.time() * 1000)

    # Apply filters
    if repo_id and status:
        issues = await issue_repo.list_by_repo(repo_id, limit)
        issues = [i for i in issues if i.status.value == status]
    elif repo_id:
        issues = await issue_repo.list_by_repo(repo_id, limit)
    elif status:
        try:
            issue_status = IssueStatus(status)
            issues = await issue_repo.list_by_status(issue_status, limit)
        except ValueError:
            return {
                "error": f"Invalid status: {status}. Valid values: open, in_progress, resolved, wontfix"
            }
    else:
        issues = await issue_repo.list_all(limit)

    duration = int(time.time() * 1000) - start

    issues_data = []
    for issue in issues:
        issues_data.append(
            {
                "issue_id": str(issue.issue_id),
                "repo_id": issue.repo_id,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status.value,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "metadata": issue.metadata,
            }
        )

    logger.info(
        "list_known_issues_executed",
        total=len(issues_data),
        repo_id=repo_id,
        status=status,
        duration_ms=duration,
    )

    return {
        "issues": issues_data,
        "total": len(issues_data),
        "filters": {
            "repo_id": repo_id,
            "status": status,
        },
    }


async def list_task_history_handler(
    outcome: str | None = None,
    tool_name: str | None = None,
    hours: int | None = None,
    limit: int = 100,
    task_repo: "TaskRepository | None" = None,
) -> dict[str, Any]:
    """List task history with optional filtering.

    This tool provides access to task history records for debugging
    and audit purposes. Can filter by outcome, tool_name, and time window.

    Args:
        outcome: Optional task outcome to filter by (success, error).
        tool_name: Optional tool name to filter by.
        hours: Optional number of hours to look back (e.g., 24 for last 24 hours).
        limit: Maximum number of records to return (default 100).
        task_repo: TaskRepository injected by the router.

    Returns:
        Dictionary with list of task records.
    """
    if task_repo is None:
        return {"error": "TaskRepository not available"}

    return await list_task_history_impl(task_repo, outcome, tool_name, hours, limit)


async def list_task_history_impl(
    task_repo: "TaskRepository",
    outcome: str | None = None,
    tool_name: str | None = None,
    hours: int | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Internal implementation for list_task_history.

    Args:
        task_repo: TaskRepository instance.
        outcome: Optional task outcome to filter by.
        tool_name: Optional tool name to filter by.
        hours: Optional number of hours to look back.
        limit: Maximum number of records to return.

    Returns:
        Task history list response.
    """
    from src.shared.models import TaskOutcome

    start = int(time.time() * 1000)

    # Apply filters
    if outcome and tool_name:
        # Get all for tool, then filter by outcome
        tasks = await task_repo.list_by_tool(tool_name, limit)
        try:
            outcome_enum = TaskOutcome(outcome)
            tasks = [t for t in tasks if t.outcome == outcome_enum]
        except ValueError:
            return {"error": f"Invalid outcome: {outcome}. Valid values: success, error"}
    elif outcome:
        try:
            outcome_enum = TaskOutcome(outcome)
            tasks = await task_repo.list_by_outcome(outcome_enum, limit)
        except ValueError:
            return {"error": f"Invalid outcome: {outcome}. Valid values: success, error"}
    elif tool_name:
        tasks = await task_repo.list_by_tool(tool_name, limit)
    elif hours:
        tasks = await task_repo.list_recent(hours, limit)
    else:
        tasks = await task_repo.list_all(limit)

    duration = int(time.time() * 1000) - start

    tasks_data = []
    for task in tasks:
        tasks_data.append(
            {
                "task_id": str(task.task_id),
                "trace_id": task.trace_id,
                "tool_name": task.tool_name,
                "caller": task.caller,
                "target_node": task.target_node,
                "target_repo": task.target_repo,
                "outcome": task.outcome.value,
                "duration_ms": task.duration_ms,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "created_at": task.created_at.isoformat(),
                "error": task.error,
                "metadata": task.metadata,
            }
        )

    logger.info(
        "list_task_history_executed",
        total=len(tasks_data),
        outcome=outcome,
        tool_name=tool_name,
        hours=hours,
        duration_ms=duration,
    )

    return {
        "tasks": tasks_data,
        "total": len(tasks_data),
        "filters": {
            "outcome": outcome,
            "tool_name": tool_name,
            "hours": hours,
        },
    }


async def get_issue_timeline_handler(
    repo_id: str | None = None,
    issue_id: str | None = None,
    limit: int = 50,
    issue_repo: "IssueRepository | None" = None,
) -> dict[str, Any]:
    """Get issue timeline/history.

    This tool provides access to issue records and their history
    for tracking purposes. Can filter by repo_id and/or issue_id.

    Args:
        repo_id: Optional repository ID to filter issues.
        issue_id: Optional specific issue ID to get timeline for.
        limit: Maximum number of issues to return (default 50).
        issue_repo: IssueRepository injected by the router.

    Returns:
        Dictionary with issue timeline data.
    """
    if issue_repo is None:
        return {"error": "IssueRepository not available"}

    return await get_issue_timeline_impl(issue_repo, repo_id, issue_id, limit)


async def get_issue_timeline_impl(
    issue_repo: "IssueRepository",
    repo_id: str | None = None,
    issue_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Internal implementation for get_issue_timeline.

    Args:
        issue_repo: IssueRepository instance.
        repo_id: Optional repository ID to filter issues.
        issue_id: Optional specific issue ID to get timeline for.
        limit: Maximum number of issues to return.

    Returns:
        Issue timeline response.
    """
    start = int(time.time() * 1000)

    if issue_id:
        # Get specific issue
        issue = await issue_repo.get(issue_id)
        duration = int(time.time() * 1000) - start

        if issue is None:
            logger.info("get_issue_timeline_not_found", issue_id=issue_id)
            return {"error": f"Issue not found: {issue_id}"}

        logger.info("get_issue_timeline_executed", issue_id=issue_id, duration_ms=duration)

        return {
            "issue": {
                "issue_id": str(issue.issue_id),
                "repo_id": issue.repo_id,
                "title": issue.title,
                "description": issue.description,
                "status": issue.status.value,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "metadata": issue.metadata,
            }
        }
    elif repo_id:
        # Get issues for specific repo
        issues = await issue_repo.list_by_repo(repo_id, limit)
        duration = int(time.time() * 1000) - start

        logger.info(
            "get_issue_timeline_by_repo_executed",
            repo_id=repo_id,
            count=len(issues),
            duration_ms=duration,
        )
    else:
        # Get all issues
        issues = await issue_repo.list_all(limit)
        duration = int(time.time() * 1000) - start

        logger.info(
            "get_issue_timeline_all_executed",
            count=len(issues),
            duration_ms=duration,
        )

    issues_data = []
    for issue in issues:
        issues_data.append(
            {
                "issue_id": str(issue.issue_id),
                "repo_id": issue.repo_id,
                "title": issue.title,
                "status": issue.status.value,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            }
        )

    return {
        "issues": issues_data,
        "total": len(issues_data),
        "filters": {
            "repo_id": repo_id,
            "issue_id": issue_id,
        },
    }
