"""Request/response schemas for hub-to-node communication."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ToolName(StrEnum):
    """Available MCP tool names."""

    LIST_REPOS = "list_repos"
    INSPECT_REPO_TREE = "inspect_repo_tree"
    READ_REPO_FILE = "read_repo_file"
    SEARCH_REPO = "search_repo"
    GIT_STATUS = "git_status"
    WRITE_MARKDOWN = "write_markdown"
    CHAT_LLM = "chat_llm"
    INDEX_REPO = "index_repo"
    GET_PROJECT_CONTEXT = "get_project_context"
    RECORD_ISSUE = "record_issue"


class NodeHealthStatus(StrEnum):
    """Health status of a node."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class ToolRequest(BaseModel):
    """Request model for tool execution across hub-to-node boundary."""

    trace_id: str = Field(..., description="Unique trace ID for request tracking")
    tool_name: ToolName = Field(..., description="Name of tool to execute")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")
    timeout: int = Field(30, description="Operation timeout in seconds")
    request_id: str | None = Field(None, description="Optional request identifier")


class ToolResponse(BaseModel):
    """Response model for tool execution across hub-to-node boundary."""

    trace_id: str = Field(..., description="Trace ID from request")
    success: bool = Field(..., description="Whether the tool executed successfully")
    result: Any | None = Field(None, description="Tool execution result")
    error: str | None = Field(None, description="Error message if failed")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class NodeHealthResponse(BaseModel):
    """Response model for node health status."""

    node_id: str = Field(..., description="Node identifier")
    status: NodeHealthStatus = Field(..., description="Current health status")
    last_check: datetime = Field(
        default_factory=datetime.utcnow, description="Last health check time"
    )
    latency_ms: int | None = Field(None, description="Response latency")
    error: str | None = Field(None, description="Error message if unhealthy")


class NodeHealthDetail(BaseModel):
    """Detailed response model for node health with all metadata."""

    node_id: str = Field(..., description="Node identifier")
    name: str = Field(..., description="Node name")
    hostname: str = Field(..., description="Node hostname")
    health_status: NodeHealthStatus = Field(..., description="Current health status")
    health_latency_ms: int | None = Field(None, description="Last health check latency")
    health_error: str | None = Field(None, description="Last health check error")
    health_check_count: int = Field(0, description="Total health checks performed")
    consecutive_failures: int = Field(0, description="Consecutive health check failures")
    last_health_check: datetime | None = Field(None, description="Last successful health check")
    last_health_attempt: datetime | None = Field(None, description="Last health check attempt")
    is_stale: bool = Field(False, description="Whether health data is stale")
    should_retry: bool = Field(True, description="Whether health check should be retried")


class FileEntry(BaseModel):
    """Single file or directory entry."""

    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path to file/directory")
    is_dir: bool = Field(..., description="Whether this is a directory")
    size: int | None = Field(None, description="File size in bytes (None for dirs)")
    modified: datetime | None = Field(None, description="Last modification time (None for dirs)")


class RepoTreeResponse(BaseModel):
    """Response model for repository tree listing."""

    repo_id: str = Field(..., description="Repository identifier")
    root_path: str = Field(..., description="Root path that was listed")
    entries: list[FileEntry] = Field(default_factory=list, description="Files and directories")
    total_count: int = Field(..., description="Total number of entries")
    truncated: bool = Field(False, description="Whether results were truncated")


class FileContentResponse(BaseModel):
    """Response model for file content reading."""

    repo_id: str = Field(..., description="Repository identifier")
    file_path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="File content")
    encoding: str = Field("utf-8", description="File encoding")
    size_bytes: int = Field(..., description="File size in bytes")
    truncated: bool = Field(False, description="Whether content was truncated")


class SearchResult(BaseModel):
    """Single search result entry."""

    file_path: str = Field(..., description="Path to file with match")
    line_number: int = Field(..., description="Line number of match")
    line_content: str = Field(..., description="Content of matching line")
    match_start: int | None = Field(None, description="Character position where match starts")
    match_end: int | None = Field(None, description="Character position where match ends")


class SearchResponse(BaseModel):
    """Response model for repository search."""

    repo_id: str = Field(..., description="Repository identifier")
    query: str = Field(..., description="Search query")
    results: list[SearchResult] = Field(default_factory=list, description="Search results")
    total_matches: int = Field(..., description="Total number of matches")
    files_searched: int = Field(..., description="Number of files searched")


class GitStatusResponse(BaseModel):
    """Response model for git status."""

    repo_id: str = Field(..., description="Repository identifier")
    branch: str = Field(..., description="Current branch name")
    is_clean: bool = Field(..., description="Whether working tree is clean")
    staged: list[str] = Field(default_factory=list, description="Staged files")
    modified: list[str] = Field(default_factory=list, description="Modified files")
    untracked: list[str] = Field(default_factory=list, description="Untracked files")
    ahead: int = Field(0, description="Number of commits ahead of remote")
    behind: int = Field(0, description="Number of commits behind remote")
