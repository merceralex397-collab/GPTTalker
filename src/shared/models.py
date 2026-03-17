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


# === Context/Vector Store Payload Models ===

# Vector dimension constant (OpenAI ada-002 compatible)
VECTOR_DIMENSION: int = 1536


class FileIndexPayload(BaseModel):
    """Payload for indexed file content in Qdrant.

    This model defines the structured metadata stored alongside
    each file's embedding vector for semantic search.
    """

    # Identification
    file_id: str = Field(..., description="Unique file identifier (hash of path)")
    repo_id: str = Field(..., description="Repository this file belongs to")
    node_id: str = Field(..., description="Node hosting this repo")

    # File metadata
    path: str = Field(..., description="Absolute file path")
    relative_path: str = Field(..., description="Relative path from repo root")
    filename: str = Field(..., description="Filename without path")
    extension: str = Field(..., description="File extension (e.g., '.py', '.md')")

    # Content metadata
    content_hash: str = Field(..., description="SHA256 hash of file content")
    size_bytes: int = Field(..., description="File size in bytes")
    line_count: int = Field(..., description="Number of lines")
    language: str | None = Field(None, description="Detected language (e.g., 'python')")

    # Indexing metadata
    indexed_at: datetime = Field(..., description="Timestamp of indexing")
    indexed_by: str = Field(..., description="Who/what triggered indexing (trace_id)")

    # Searchable text (for hybrid search if needed)
    content_preview: str | None = Field(
        None, description="First N chars for preview (truncated for storage)"
    )

    # Provenance
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class IssueIndexPayload(BaseModel):
    """Payload for indexed issues in Qdrant.

    This model defines the structured metadata stored alongside
    each issue's embedding vector for semantic search.
    """

    # Identification
    issue_id: str = Field(..., description="Unique issue identifier (matches SQLite)")
    repo_id: str = Field(..., description="Repository this issue belongs to")

    # Issue content (semantic search target)
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description (full text)")

    # Status tracking
    status: str = Field(..., description="Issue status (open, in_progress, resolved, wontfix)")

    # Timestamps
    created_at: datetime = Field(..., description="Issue creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    indexed_at: datetime = Field(..., description="Timestamp of Qdrant indexing")

    # Provenance
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# === Task Classification Models (SCHED-001) ===


class TaskClass(StrEnum):
    """Valid task class values for LLM routing.

    These classifications determine which LLM service type is selected
    for a given request based on the workload characteristics.
    """

    CODING = "coding"  # Code generation, editing, review
    CHAT = "chat"  # General conversation
    EMBEDDING = "embedding"  # Text vectorization
    SUMMARIZATION = "summarize"  # Document summarization
    REASONING = "reasoning"  # Complex reasoning workloads
    SEARCH = "search"  # Semantic search queries


class TaskClassification(BaseModel):
    """Classification result for a task.

    This model represents the determined task type along with
    confidence and reasoning for the classification.
    """

    task_class: TaskClass = Field(..., description="The classified task type")
    confidence: float = Field(
        1.0, description="Classification confidence (0.0-1.0)", ge=0.0, le=1.0
    )
    reasoning: str | None = Field(
        None, description="Explanation for why this classification was chosen"
    )


class ServiceCapabilities(BaseModel):
    """Capabilities metadata for an LLM service.

    This model defines what capabilities a service supports,
    enabling intelligent routing decisions based on workload requirements.
    """

    supports_streaming: bool = Field(False, description="Whether service supports streaming")
    max_tokens: int | None = Field(None, description="Maximum tokens in a single request")
    context_window: int | None = Field(None, description="Maximum context window size in tokens")
    recommended_for: list[TaskClass] = Field(
        default_factory=list, description="Task classes this service is recommended for"
    )


# === Helper Functions ===


def generate_file_id(repo_id: str, relative_path: str) -> str:
    """Generate unique file ID from repo and path.

    Args:
        repo_id: Repository identifier.
        relative_path: Relative path from repo root.

    Returns:
        Unique file identifier (32 hex chars).
    """
    import hashlib

    key = f"{repo_id}:{relative_path}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of file content.

    Args:
        content: File content as string.

    Returns:
        SHA256 hash as hex string.
    """
    import hashlib

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class SearchFilter(BaseModel):
    """Filter parameters for context search operations."""

    repo_id: str | None = Field(None, description="Filter by repository ID")
    node_id: str | None = Field(None, description="Filter by node ID")
    extension: str | None = Field(None, description="Filter by file extension")
    language: str | None = Field(None, description="Filter by programming language")
    status: str | None = Field(None, description="Filter by issue status")
    min_size_bytes: int | None = Field(None, description="Minimum file size in bytes")
    max_size_bytes: int | None = Field(None, description="Maximum file size in bytes")
    created_after: datetime | None = Field(None, description="Filter by created after timestamp")
    created_before: datetime | None = Field(None, description="Filter by created before timestamp")


# === Context Bundle Models ===


# Bundle type enumeration
class BundleType(StrEnum):
    """Valid context bundle types."""

    TASK = "task"
    REVIEW = "review"
    RESEARCH = "research"


class BundleSource(BaseModel):
    """Source tracking for a single item in a bundle.

    This model tracks the provenance of each piece of context
    included in a bundle.
    """

    source_type: str = Field(..., description="Source type: file, issue, commit")
    source_id: str = Field(..., description="Unique identifier of the source")
    repo_id: str = Field(..., description="Repository the source belongs to")
    node_id: str = Field(..., description="Node hosting the repo")
    included_at: datetime = Field(..., description="When the source was added to bundle")
    relevance_score: float | None = Field(None, description="Similarity score from semantic search")
    reason: str | None = Field(None, description="Natural language explanation for inclusion")


class ContextBundlePayload(BaseModel):
    """Payload for a context bundle stored in Qdrant.

    This model defines the structured metadata stored alongside
    each bundle for retrieval and provenance tracking.
    """

    # Bundle identification
    bundle_id: str = Field(..., description="Unique bundle identifier")
    bundle_type: BundleType = Field(..., description="Type of bundle: task, review, research")
    title: str = Field(..., description="Human-readable bundle title")
    description: str | None = Field(None, description="Bundle description")

    # Creation metadata
    created_at: datetime = Field(..., description="Bundle creation timestamp")
    created_by: str = Field(..., description="Trace ID of creator")

    # Bundle composition
    repo_ids: list[str] = Field(default_factory=list, description="Repos included in bundle")
    file_ids: list[str] = Field(default_factory=list, description="File IDs in bundle")
    issue_ids: list[str] = Field(default_factory=list, description="Issue IDs in bundle")

    # Provenance tracking
    sources: list[BundleSource] = Field(
        default_factory=list, description="Source tracking for bundle items"
    )

    # Optional task metadata
    task_type: str | None = Field(None, description="Task type if bundle_type is task")
    priority: str | None = Field(None, description="Priority level if bundle_type is task")
    generation_method: str = Field(
        "semantic_similarity", description="How the bundle was assembled"
    )


# === Recurring Issue Aggregation Models ===


# Aggregation type enumeration
class AggregationType(StrEnum):
    """Valid aggregation types for recurring issues."""

    EXACT_TITLE = "exact_title"
    SEMANTIC = "semantic"
    TAG = "tag"


class RecurringIssueGroup(BaseModel):
    """A group of recurring issues identified by aggregation.

    This model represents a collection of issues that share
    common characteristics (exact title, semantic similarity, or tags).
    """

    # Group identification
    group_id: str = Field(..., description="Unique group identifier")
    aggregation_type: AggregationType = Field(..., description="Method used to form this group")

    # Representative issue (first one by creation date)
    representative_title: str = Field(..., description="Title representing the group")
    count: int = Field(..., description="Number of issues in this group")

    # Issue details
    issue_ids: list[str] = Field(default_factory=list, description="Issue IDs in this group")
    repo_ids: list[str] = Field(default_factory=list, description="Repos with issues in this group")

    # Temporal span
    first_seen: datetime = Field(..., description="Oldest issue in group")
    last_seen: datetime = Field(..., description="Most recent issue in group")

    # Computed fields
    total_duration_days: int | None = Field(None, description="Days between first and last issue")


class AggregationSummary(BaseModel):
    """Summary statistics for recurring issue aggregation."""

    total_groups: int = Field(..., description="Number of issue groups found")
    total_issues_aggregated: int = Field(..., description="Total issues in all groups")
    open_issues: int = Field(..., description="Issues still open")
    resolved_issues: int = Field(..., description="Issues resolved")
    wontfix_issues: int = Field(..., description="Issues marked wontfix")


# === Cross-Repo Search Models ===


class RepoOwner(BaseModel):
    """Structured owner information for a repository."""

    owner_id: str = Field(..., description="Unique owner identifier")
    name: str = Field(..., description="Human-readable owner name")
    email: str | None = Field(None, description="Owner email")
    role: str = Field("maintainer", description="Owner role: maintainer, contributor, observer")
    added_at: datetime = Field(default_factory=datetime.utcnow, description="When owner was added")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional owner metadata")


class RepoMetadata(BaseModel):
    """Metadata summary for a single repo in cross-repo results."""

    repo_id: str = Field(..., description="Repository identifier")
    node_id: str = Field(..., description="Node hosting this repo")
    file_count: int = Field(0, description="Number of indexed files")
    issue_count: int = Field(0, description="Number of indexed issues")
    last_indexed_at: datetime | None = Field(None, description="Last indexing timestamp")
    languages: list[str] = Field(default_factory=list, description="Detected languages")
    # Extended fields for XREPO-002
    owner: RepoOwner | None = Field(None, description="Owner information for this repo")


class FileSearchHit(BaseModel):
    """Individual file hit from cross-repo search."""

    file_id: str = Field(..., description="Unique file identifier")
    repo_id: str = Field(..., description="Repository identifier")
    node_id: str = Field(..., description="Node hosting this repo")
    path: str = Field(..., description="Absolute file path")
    relative_path: str = Field(..., description="Relative path from repo root")
    filename: str = Field(..., description="Filename without path")
    extension: str = Field(..., description="File extension")
    language: str | None = Field(None, description="Detected programming language")
    score: float = Field(..., description="Similarity score")
    content_preview: str | None = Field(None, description="Content preview")


class CrossRepoSearchResult(BaseModel):
    """Aggregated search result from cross-repo search."""

    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Total results found")
    repos_searched: int = Field(..., description="Number of repos searched")
    repo_metadata: list[RepoMetadata] = Field(
        default_factory=list, description="Metadata for each searched repo"
    )
    file_results: list[FileSearchHit] = Field(
        default_factory=list, description="File hits from search"
    )
    latency_ms: int = Field(..., description="Search latency in milliseconds")


class RelatedRepo(BaseModel):
    """A repository related to another via shared content."""

    repo_id: str = Field(..., description="Related repository identifier")
    node_id: str = Field(..., description="Node hosting this repo")
    relationship_type: str = Field(..., description="Type of relationship: files, issues, bundles")
    overlap_score: float = Field(..., description="Similarity/overlap score")
    shared_file_count: int | None = Field(
        None, description="Number of shared files (for file relationships)"
    )
    shared_issue_count: int | None = Field(
        None, description="Number of shared issues (for issue relationships)"
    )


# === Relationship and Landscape Models ===


class RelationshipType(StrEnum):
    """Valid relationship types between repositories."""

    DEPENDS_ON = "depends_on"  # Repo A depends on Repo B
    RELATED_TO = "related_to"  # General relationship (shared code, similar domain)
    FORKS_FROM = "forks_from"  # Repo A is a fork of Repo B
    CONTAINS = "contains"  # Repo A contains Repo B as submodule
    REFERENCES = "references"  # Repo A references Repo B (imports, docs)
    SHARED_DEPENDENCY = "shared_dep"  # Both repos share a dependency


class RepoRelationship(BaseModel):
    """Explicit relationship between two repositories."""

    relationship_id: str = Field(..., description="Unique relationship identifier")
    source_repo_id: str = Field(..., description="Source repository ID")
    target_repo_id: str = Field(..., description="Target repository ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")

    # Relationship metadata
    description: str | None = Field(None, description="Human-readable relationship description")
    confidence: float = Field(1.0, description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    bidirectional: bool = Field(False, description="Whether relationship applies both ways")

    # Provenance
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: str = Field(..., description="Who created this relationship (trace_id)")
    source_record: str | None = Field(
        None, description="Source record citation (e.g., 'git log', 'import scan', 'manual')"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LandscapeSource(BaseModel):
    """Source citation for a landscape or cross-repo view."""

    source_type: str = Field(..., description="Type of source: repo, relationship, issue, file")
    source_id: str = Field(..., description="Unique identifier of the source")
    repo_id: str = Field(..., description="Repository the source belongs to")
    node_id: str = Field(..., description="Node hosting the repo")
    citation: str = Field(..., description="Human-readable citation text")
    included_at: datetime = Field(default_factory=datetime.utcnow, description="When included")


class LandscapeMetadata(BaseModel):
    """Extended landscape metadata with ownership and sources."""

    # Ownership
    owner: RepoOwner | None = Field(None, description="Primary owner of this landscape view")
    maintainers: list[RepoOwner] = Field(default_factory=list, description="All maintainers")

    # Provenance tracking
    sources: list[LandscapeSource] = Field(
        default_factory=list, description="Source records cited in this landscape"
    )
    relationship_count: int = Field(0, description="Number of explicit relationships included")

    # Extended metadata
    description: str | None = Field(None, description="Landscape description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    category: str | None = Field(
        None, description="Category (e.g., 'frontend', 'backend', 'infrastructure')"
    )


class ProjectLandscape(BaseModel):
    """Overview of all accessible repositories with metadata."""

    total_repos: int = Field(..., description="Total number of accessible repos")
    total_files: int = Field(..., description="Total indexed files across all repos")
    total_issues: int = Field(..., description="Total indexed issues across all repos")
    repos: list[RepoMetadata] = Field(
        default_factory=list, description="Metadata for each accessible repo"
    )
    relationships: list[RelatedRepo] | None = Field(
        None, description="Optional relationship data between repos"
    )
    # Extended fields for XREPO-002
    landscape_metadata: LandscapeMetadata | None = Field(
        None, description="Extended landscape metadata with ownership and sources"
    )


# === Architecture Map Models (XREPO-003) ===


class ArchitectureNode(BaseModel):
    """Node representing a single repo in the architecture view."""

    repo_id: str = Field(..., description="Repository identifier")
    node_id: str = Field(..., description="Node hosting this repo")
    name: str = Field(..., description="Human-readable repo name")
    language_distribution: dict[str, int] = Field(
        default_factory=dict, description="Language to file count mapping"
    )
    file_count: int = Field(0, description="Number of indexed files")
    issue_count: int = Field(0, description="Number of indexed issues")
    owner: RepoOwner | None = Field(None, description="Owner information for this repo")
    category: str | None = Field(
        None, description="Inferred or explicit category (frontend, backend, etc.)"
    )


class ArchitectureEdge(BaseModel):
    """Edge representing a relationship between two repos in the architecture."""

    source_repo_id: str = Field(..., description="Source repository ID")
    target_repo_id: str = Field(..., description="Target repository ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    confidence: float = Field(1.0, description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    description: str | None = Field(None, description="Human-readable relationship description")


class ArchitectureMap(BaseModel):
    """Complete architecture map with nodes, edges, and metadata."""

    nodes: list[ArchitectureNode] = Field(
        default_factory=list, description="Architecture nodes (repos)"
    )
    edges: list[ArchitectureEdge] = Field(
        default_factory=list, description="Architecture edges (relationships)"
    )
    total_repos: int = Field(..., description="Total number of repos in the map")
    total_files: int = Field(..., description="Total indexed files across all repos")
    language_summary: dict[str, int] = Field(
        default_factory=dict, description="Aggregated language distribution"
    )
    landscape_metadata: LandscapeMetadata = Field(
        ..., description="Landscape metadata with sources and ownership"
    )


# === Distributed Scheduler Models (SCHED-002) ===]


class SchedulerInput(BaseModel):
    """All inputs required for distributed scheduling decision.

    This model captures all decision factors for the distributed scheduler,
    including task classification, service preferences, node preferences,
    capability requirements, and scheduling constraints.
    """

    # Task classification (from SCHED-001)
    task_class: TaskClass = Field(TaskClass.CHAT, description="Task type for routing")

    # Service preferences
    preferred_service_id: str | None = Field(None, description="Explicit service ID to use")
    preferred_service_type: LLMServiceType | None = Field(
        None, description="Explicit service type to prefer"
    )

    # Node preferences
    preferred_node_id: str | None = Field(None, description="Explicit node ID to prefer")
    exclude_node_ids: list[str] = Field(
        default_factory=list, description="Nodes to exclude from selection"
    )

    # Capability requirements
    required_capabilities: list[str] = Field(
        default_factory=list, description="Required service capabilities"
    )

    # Scheduling constraints
    max_latency_ms: int | None = Field(
        None, description="Maximum acceptable node latency in milliseconds"
    )
    allow_fallback: bool = Field(True, description="Whether to fallback on failure")
    max_fallback_attempts: int = Field(3, ge=1, le=10, description="Maximum fallback attempts")

    # Context
    trace_id: str | None = Field(None, description="Trace ID for logging")


class SchedulerResult(BaseModel):
    """Result of a scheduling decision.

    This model contains the selected service and node, along with
    health information and the fallback chain for retry scenarios.
    """

    selected_service: LLMServiceInfo = Field(..., description="Selected LLM service")
    selected_node: NodeInfo = Field(..., description="Node hosting the selected service")
    node_health: "NodeHealthInfo | None" = Field(None, description="Node health status")
    fallback_chain: list["SchedulerResult"] = Field(
        default_factory=list, description="Ordered fallback options"
    )
    selection_reason: str = Field(..., description="Human-readable selection reason")
    latency_ms: int | None = Field(None, description="Expected latency based on health check")


class NodeHealthInfo(BaseModel):
    """Compact node health information for scheduler decisions.

    This model contains the essential health data needed for
    scheduling decisions without exposing full NodeHealth details.
    """

    node_id: str = Field(..., description="Node identifier")
    health_status: NodeStatus = Field(NodeStatus.UNKNOWN, description="Current health status")
    is_healthy: bool = Field(False, description="Whether node is healthy enough for routing")
    latency_ms: int | None = Field(None, description="Last known latency in milliseconds")
    is_stale: bool = Field(False, description="Whether health data is stale")


class ServiceNodePair(BaseModel):
    """Pairing of a service with its hosting node.

    This helper class represents a candidate for scheduling,
    combining service and node information with health status.
    """

    service: LLMServiceInfo = Field(..., description="LLM service")
    node: NodeInfo = Field(..., description="Hosting node")
    health: NodeHealthInfo | None = Field(None, description="Node health information")
    reason: str = Field("", description="Reason for this candidate being available")


# === Observability Models (OBS-001) ===


class DocOwner(BaseModel):
    """Owner information for generated documents."""

    owner_id: str = Field(..., description="Unique owner identifier")
    name: str = Field(..., description="Human-readable owner name")
    email: str | None = Field(None, description="Owner email")
    role: str = Field("generator", description="Role: generator, reviewer, approver")
    added_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedDocRecord(BaseModel):
    """Record of a generated/delivered document."""

    doc_id: UUID = Field(..., description="Unique document identifier")
    trace_id: str | None = Field(None, description="Trace ID for request tracking")
    tool_name: str = Field(..., description="Tool that generated this doc (e.g., write_markdown)")
    caller: str = Field(..., description="Caller identifier")
    target_path: str = Field(..., description="Path where document was written")
    content_hash: str = Field(..., description="SHA256 hash of document content")
    size_bytes: int = Field(..., description="Document size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventType(StrEnum):
    """Valid audit event types."""

    TASK_EXECUTED = "task_executed"
    DOC_GENERATED = "doc_generated"
    POLICY_REJECTED = "policy_rejected"
    NODE_ACCESS = "node_access"
    REPO_ACCESS = "repo_access"
    LLM_REQUEST = "llm_request"
    INDEXING_RUN = "indexing_run"
    CONFIG_CHANGED = "config_changed"


class AuditRecord(BaseModel):
    """Audit log entry with full trace context."""

    audit_id: UUID = Field(..., description="Unique audit identifier")
    trace_id: str | None = Field(None, description="Trace ID linking to task")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    actor: str = Field(..., description="Who triggered this event")
    target_type: str = Field(..., description="Target type: node, repo, doc, service")
    target_id: str | None = Field(None, description="Target identifier")
    action: str = Field(..., description="Action performed")
    outcome: str = Field(..., description="Outcome: success, failure, rejected")
    duration_ms: int | None = Field(None, description="Event duration")
    error: str | None = Field(None, description="Error message if failed")
    trace_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
