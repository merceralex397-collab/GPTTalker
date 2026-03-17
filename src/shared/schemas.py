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


class NodeListResponse(BaseModel):
    """Response model for list_nodes tool."""

    nodes: list[dict[str, Any]] = Field(
        default_factory=list, description="List of nodes with health metadata"
    )
    total: int = Field(0, description="Total number of nodes")


class RepoListResponse(BaseModel):
    """Response model for list_repos tool."""

    repos: list[dict[str, Any]] = Field(
        default_factory=list, description="List of approved repositories"
    )
    total: int = Field(0, description="Total number of repositories")
    filtered_by_node: str | None = Field(None, description="Node ID if repos were filtered by node")


class ChatLLMRequest(BaseModel):
    """Request model for chat_llm tool."""

    service_id: str | None = Field(None, description="LLM service identifier")
    service_name: str | None = Field(
        None, description="LLM service name (alternative to service_id)"
    )
    prompt: str = Field(..., description="Prompt to send to LLM")
    max_tokens: int = Field(1000, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Sampling temperature")
    session_id: str | None = Field(
        None, description="Optional session ID for conversation continuity"
    )
    system_prompt: str | None = Field(None, description="Optional system prompt")


class ChatLLMResponse(BaseModel):
    """Response model for chat_llm tool."""

    success: bool = Field(..., description="Whether the request succeeded")
    response: str | None = Field(None, description="LLM response text")
    model: str | None = Field(None, description="Model that generated the response")
    service_id: str = Field(..., description="Service ID that handled the request")
    service_name: str | None = Field(None, description="Human-readable service name")
    latency_ms: int = Field(..., description="Request latency in milliseconds")
    tokens_used: int | None = Field(None, description="Total tokens used")
    finish_reason: str | None = Field(None, description="Reason for completion")
    error: str | None = Field(None, description="Error message if failed")


# === Context and Issue Schemas ===)


class GetProjectContextParams(BaseModel):
    """Parameters for get_project_context tool."""

    query: str = Field(..., description="Natural language search query")
    repo_id: str | None = Field(None, description="Filter by specific repository")
    node_id: str | None = Field(None, description="Filter by specific node")
    limit: int = Field(10, description="Maximum results", ge=1, le=100)
    score_threshold: float | None = Field(
        None, description="Minimum similarity score", ge=0.0, le=1.0
    )


class ContextSearchResult(BaseModel):
    """Single context search result with provenance."""

    file_id: str = Field(..., description="Unique file identifier")
    repo_id: str = Field(..., description="Repository identifier")
    node_id: str = Field(..., description="Node hosting the repo")
    path: str = Field(..., description="Absolute file path")
    relative_path: str = Field(..., description="Path relative to repo root")
    filename: str = Field(..., description="Filename without path")
    extension: str = Field(..., description="File extension")
    language: str | None = Field(None, description="Detected language")
    content_hash: str = Field(..., description="SHA256 of content")
    size_bytes: int = Field(..., description="File size in bytes")
    line_count: int = Field(..., description="Number of lines")
    indexed_at: datetime = Field(..., description="When file was indexed")
    score: float = Field(..., description="Similarity score")
    content_preview: str | None = Field(None, description="Content preview")


class GetProjectContextResponse(BaseModel):
    """Response for get_project_context tool."""

    query: str = Field(..., description="Original search query")
    results: list[ContextSearchResult] = Field(
        default_factory=list, description="Search results with provenance"
    )
    total: int = Field(..., description="Total matches found")
    repo_id: str | None = Field(None, description="Filter used")
    latency_ms: int = Field(..., description="Search latency")


class RecordIssueParams(BaseModel):
    """Parameters for record_issue tool."""

    repo_id: str = Field(..., description="Repository identifier")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    status: str = Field("open", description="Issue status")
    metadata: dict | None = Field(None, description="Additional metadata")


class RecordIssueResponse(BaseModel):
    """Response for record_issue tool."""

    success: bool = Field(..., description="Whether the issue was created")
    issue_id: str = Field(..., description="Created issue identifier")
    repo_id: str = Field(..., description="Repository the issue belongs to")
    title: str = Field(..., description="Issue title")
    indexed: bool = Field(..., description="Whether issue was indexed in Qdrant")
    error: str | None = Field(None, description="Error message if failed")
