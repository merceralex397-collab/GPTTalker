"""Node-specific Pydantic models for the node agent."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response for node agent."""

    status: Literal["healthy", "degraded", "unhealthy"]
    node_name: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    capabilities: list[str] = Field(
        default_factory=lambda: ["repo_read", "repo_search", "markdown_write"]
    )
    checks: dict[str, bool] = Field(default_factory=dict)


class OperationRequest(BaseModel):
    """Base class for operation requests."""

    path: str = Field(..., description="Path for the operation")


class ListDirRequest(OperationRequest):
    """Request to list directory contents."""

    pass


class ReadFileRequest(OperationRequest):
    """Request to read a file."""

    offset: int = Field(0, ge=0, description="Byte offset to start reading from")
    limit: int | None = Field(None, ge=1, description="Maximum bytes to read")


class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str = Field(..., description="Directory to search in")
    pattern: str = Field(..., description="Search pattern (regex)")
    include_patterns: list[str] | None = Field(
        None, description="File patterns to include (e.g., ['*.py', '*.md'])"
    )
    mode: str = Field("text", description="Search mode: text, path, or symbol")
    max_results: int = Field(1000, ge=1, le=1000, description="Maximum matches to return")
    timeout: int = Field(60, ge=1, le=120, description="Search timeout in seconds")


class GitStatusRequest(OperationRequest):
    """Request to get git status."""

    pass


class WriteFileRequest(BaseModel):
    """Request to write a file."""

    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="Content to write")


class OperationResponse(BaseModel):
    """Base response for operations."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable message")
    data: dict | list | str | None = Field(None, description="Operation-specific data payload")


class ListDirResponse(OperationResponse):
    """Response for list directory operation."""

    data: list[str] | None = Field(None, description="List of file/directory names")


class ReadFileResponse(OperationResponse):
    """Response for read file operation."""

    data: str | None = Field(None, description="File contents")
    size: int | None = Field(None, description="Size of file in bytes")
    truncated: bool = Field(False, description="Whether content was truncated")


class SearchResult(BaseModel):
    """Single search result."""

    file: str = Field(..., description="File path")
    line: int = Field(..., description="Line number")
    content: str = Field(..., description="Line content")


class SearchResponse(OperationResponse):
    """Response for search operation."""

    data: list[SearchResult] | None = Field(None, description="List of search results")


class GitStatusResponse(OperationResponse):
    """Response for git status operation."""

    data: dict[str, Any] | None = Field(None, description="Git status information")


class WriteFileResponse(OperationResponse):
    """Response for write file operation."""

    data: dict[str, Any] | None = Field(None, description="Write result with verification metadata")
