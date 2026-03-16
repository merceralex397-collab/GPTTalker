"""Shared Pydantic models for GPTTalker."""

import re
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NodeStatus(StrEnum):
    """Valid node status values."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class TaskOutcome(StrEnum):
    """Valid task outcome values."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    REJECTED = "rejected"


class IssueStatus(StrEnum):
    """Valid issue status values."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wontfix"


class LLMServiceType(StrEnum):
    """Valid LLM service type values."""

    OPENCODE = "opencode"
    LLAMA = "llama"
    EMBEDDING = "embedding"
    HELPER = "helper"


class TraceMixin(BaseModel):
    """Mixin for adding trace ID to models."""

    trace_id: str | None = Field(None, description="Unique trace ID for request tracking")


class NodeInfo(BaseModel):
    """Information about a managed node."""

    node_id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Human-readable node name")
    hostname: str = Field(..., description="Node hostname or IP")
    status: NodeStatus = Field(NodeStatus.UNKNOWN, description="Current node status")
    last_seen: datetime | None = Field(None, description="Last time node was seen")

    @field_validator("node_id")
    @classmethod
    def validate_node_id(cls, v: str) -> str:
        """Validate node_id matches allowed pattern."""
        if not v or not isinstance(v, str):
            raise ValueError("node_id must be a non-empty string")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("node_id must match pattern ^[a-zA-Z0-9_-]+$")
        return v


class RepoInfo(BaseModel):
    """Information about a tracked repository."""

    repo_id: str = Field(..., description="Unique repo identifier")
    name: str = Field(..., description="Human-readable repo name")
    path: str = Field(..., description="Absolute path to repo")
    node_id: str = Field(..., description="Node that hosts this repo")
    is_indexed: bool = Field(False, description="Whether repo is indexed in Qdrant")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path is absolute."""
        import os

        if not v or not isinstance(v, str):
            raise ValueError("path must be a non-empty string")
        if not os.path.isabs(v):
            raise ValueError("path must be an absolute path")
        return v


class WriteTargetInfo(BaseModel):
    """Information about an allowed write target."""

    target_id: str = Field(..., description="Unique target identifier")
    path: str = Field(..., description="Absolute path to write target")
    allowed_extensions: list[str] = Field([".md", ".txt"], description="Allowed file extensions")

    @field_validator("target_id")
    @classmethod
    def validate_target_id(cls, v: str) -> str:
        """Validate target_id matches allowed pattern."""
        if not v or not isinstance(v, str):
            raise ValueError("target_id must be a non-empty string")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("target_id must match pattern ^[a-zA-Z0-9_-]+$")
        return v

    @field_validator("allowed_extensions")
    @classmethod
    def validate_extensions(cls, v: list[str]) -> list[str]:
        """Validate all extensions start with dot."""
        for ext in v:
            if not ext.startswith("."):
                raise ValueError(f"Extension '{ext}' must start with '.'")
        return v


class LLMServiceInfo(BaseModel):
    """Information about an LLM service alias."""

    service_id: str = Field(..., description="Unique service identifier")
    name: str = Field(..., description="Human-readable service name")
    type: LLMServiceType = Field(..., description="Type of LLM service")
    endpoint: str | None = Field(None, description="Service endpoint URL")
    api_key: str | None = Field(None, description="API key for service (NOT logged)")

    model_config = {"exclude_from_logging": ["api_key"]}


class TaskRecord(BaseModel):
    """Record of a completed task."""

    task_id: UUID = Field(..., description="Unique task identifier")
    trace_id: str | None = Field(None, description="Trace ID for request tracking")
    tool_name: str = Field(..., description="Name of tool that was called")
    caller: str = Field(..., description="Caller identifier")
    target_node: str | None = Field(None, description="Target node if applicable")
    target_repo: str | None = Field(None, description="Target repo if applicable")
    outcome: TaskOutcome = Field(..., description="Task outcome")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    started_at: datetime | None = Field(
        None, description="Task start time for duration calculation"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Task creation timestamp"
    )
    error: str | None = Field(None, description="Error message if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class IssueRecord(BaseModel):
    """Record of a known issue."""

    issue_id: UUID = Field(..., description="Unique issue identifier")
    repo_id: str = Field(..., description="Repo this issue belongs to")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    status: IssueStatus = Field(IssueStatus.OPEN, description="Current issue status")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Issue creation timestamp"
    )
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
