"""Tool registration for MCP discovery tools."""

from src.hub.tool_router import ToolRegistry
from src.hub.tool_routing.requirements import (
    LLM_REQUIREMENT,
    NO_POLICY_REQUIREMENT,
    READ_NODE_REQUIREMENT,
    READ_REPO_REQUIREMENT,
    WRITE_REQUIREMENT,
)


def register_discovery_tools(registry: ToolRegistry) -> None:
    """Register discovery tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    # Import handlers here to avoid circular imports
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.discovery import list_nodes_handler, list_repos_handler

    # Register list_nodes tool
    # Policy: NO_POLICY_REQUIREMENT - discovery tool that lists all nodes
    # This provides general overview without accessing specific node resources
    registry.register(
        ToolDefinition(
            name="list_nodes",
            description="List all registered nodes with their health status. "
            "Returns information about each node including name, hostname, "
            "status, and detailed health metadata.",
            handler=list_nodes_handler,
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            policy=NO_POLICY_REQUIREMENT,
        )
    )

    # Register list_repos tool
    # Policy: READ_NODE_REQUIREMENT - requires valid node access when node_id provided
    # When node_id is omitted, returns all approved repos from the registry
    registry.register(
        ToolDefinition(
            name="list_repos",
            description="List all approved repositories. Optionally filter by node_id "
            "to see repos on a specific machine.",
            handler=list_repos_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Optional node_id to filter repos by specific node",
                    }
                },
                "required": [],
            },
            policy=READ_NODE_REQUIREMENT,
        )
    )


def register_inspection_tools(registry: ToolRegistry) -> None:
    """Register inspection tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.inspection import (
        inspect_repo_tree_handler,
        read_repo_file_handler,
    )

    # Register inspect_repo_tree tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="inspect_repo_tree",
            description="List directory contents within an approved repository. "
            "Returns file and directory entries with metadata (name, path, is_dir, size, modified). "
            "Use max_entries to limit results. Requires node_id and repo_id for access control.",
            handler=inspect_repo_tree_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node identifier (required)",
                    },
                    "repo_id": {
                        "type": "string",
                        "description": "Repository identifier (required)",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to repo root (default: root)",
                        "default": "",
                    },
                    "max_entries": {
                        "type": "integer",
                        "description": "Maximum entries to return",
                        "default": 100,
                        "maximum": 500,
                    },
                },
                "required": ["node_id", "repo_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register read_repo_file tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="read_repo_file",
            description="Read file contents from an approved repository. "
            "Returns file content with metadata including encoding, size_bytes, and truncated flag. "
            "Supports offset and limit for reading file segments. Requires node_id, repo_id, and file_path for access control.",
            handler=read_repo_file_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node identifier (required)",
                    },
                    "repo_id": {
                        "type": "string",
                        "description": "Repository identifier (required)",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "File path relative to repo root (required)",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Byte offset to start reading from",
                        "default": 0,
                        "minimum": 0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum bytes to read (None for entire file)",
                        "default": None,
                        "minimum": 1,
                    },
                },
                "required": ["node_id", "repo_id", "file_path"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )


def register_observability_tools(registry: ToolRegistry) -> None:
    """Register observability tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.observability import (
        get_issue_timeline_handler,
        get_task_details_handler,
        list_known_issues_handler,
        list_task_history_handler,
        list_generated_docs_handler,
    )

    # Register get_task_details tool
    # Policy: NO_POLICY_REQUIREMENT - observability read tool
    registry.register(
        ToolDefinition(
            name="get_task_details",
            description="Get detailed information about a specific task by task_id or trace_id. "
            "Returns full task record including metadata, timing, and outcome.",
            handler=get_task_details_handler,
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Specific task ID to look up",
                    },
                    "trace_id": {
                        "type": "string",
                        "description": "Trace ID to search for related tasks",
                    },
                },
                "required": [],
            },
            policy=NO_POLICY_REQUIREMENT,
        )
    )

    # Register list_generated_docs tool
    # Policy: NO_POLICY_REQUIREMENT - observability read tool
    registry.register(
        ToolDefinition(
            name="list_generated_docs",
            description="List generated document history. "
            "Returns records of all documents generated by hub tools, "
            "including file paths, content hashes, and creation timestamps.",
            handler=list_generated_docs_handler,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Filter by specific tool name",
                    },
                    "caller": {
                        "type": "string",
                        "description": "Filter by caller identifier",
                    },
                },
                "required": [],
            },
            policy=NO_POLICY_REQUIREMENT,
        )
    )

    # Register get_issue_timeline tool
    # Policy: NO_POLICY_REQUIREMENT - observability read tool
    registry.register(
        ToolDefinition(
            name="get_issue_timeline",
            description="Get issue timeline and history. "
            "Returns issue records with their status, timestamps, and metadata. "
            "Can filter by repo_id or get a specific issue by issue_id.",
            handler=get_issue_timeline_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Filter by specific repository ID",
                    },
                    "issue_id": {
                        "type": "string",
                        "description": "Specific issue ID to get timeline for",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                    },
                },
                "required": [],
            },
            policy=NO_POLICY_REQUIREMENT,
        )
    )

    # Register list_known_issues tool
    # Policy: NO_POLICY_REQUIREMENT - observability read tool
    registry.register(
        ToolDefinition(
            name="list_known_issues",
            description="List known issues with optional filtering. "
            "Returns issue records from the issue tracking system, "
            "including title, description, status, and timestamps. "
            "Can filter by repo_id and/or status.",
            handler=list_known_issues_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Filter by specific repository ID",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by issue status",
                        "enum": ["open", "in_progress", "resolved", "wontfix"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                    },
                },
                "required": [],
            },
            policy=NO_POLICY_REQUIREMENT,
        )
    )

    # Register list_task_history tool
    # Policy: NO_POLICY_REQUIREMENT - observability read tool
    registry.register(
        ToolDefinition(
            name="list_task_history",
            description="List task history with optional filtering. "
            "Returns records of all tool executions including tool name, "
            "outcome, duration, and timestamps. "
            "Can filter by outcome, tool_name, and time window.",
            handler=list_task_history_handler,
            parameters={
                "type": "object",
                "properties": {
                    "outcome": {
                        "type": "string",
                        "description": "Filter by task outcome",
                        "enum": ["success", "error"],
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Filter by specific tool name",
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Filter by time window (last N hours)",
                        "minimum": 1,
                        "maximum": 8760,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 500,
                    },
                },
                "required": [],
            },
            policy=NO_POLICY_REQUIREMENT,
        )
    )


def register_search_tools(registry: ToolRegistry) -> None:
    """Register search and git operation tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.git_operations import git_status_handler
    from src.hub.tools.search import search_repo_handler

    # Register search_repo tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="search_repo",
            description="Search for text patterns in files within an approved repository. "
            "Uses ripgrep for efficient regex search. Supports file pattern filtering "
            "(e.g., *.py, *.md). Returns matches with file path, line number, and content. "
            "Requires node_id and repo_id for access control.",
            handler=search_repo_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node identifier (required)",
                    },
                    "repo_id": {
                        "type": "string",
                        "description": "Repository identifier (required)",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for (required)",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to repo root (default: root)",
                        "default": "",
                    },
                    "include_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File patterns to include (e.g., ['*.py', '*.md'])",
                        "default": None,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum matches to return",
                        "default": 1000,
                        "maximum": 1000,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Search timeout in seconds",
                        "default": 60,
                        "maximum": 120,
                    },
                    "mode": {
                        "type": "string",
                        "description": "Search mode: text (content), path (filenames), symbol (identifiers)",
                        "default": "text",
                        "enum": ["text", "path", "symbol"],
                    },
                },
                "required": ["node_id", "repo_id", "pattern"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register git_status tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="git_status",
            description="Get git status for an approved repository. "
            "Returns current branch, clean/dirty status, staged/modified/untracked files, "
            "and ahead/behind count relative to remote. This is a read-only operation. "
            "Requires node_id and repo_id for access control.",
            handler=git_status_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Node identifier (required)",
                    },
                    "repo_id": {
                        "type": "string",
                        "description": "Repository identifier (required)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Git operation timeout in seconds",
                        "default": 30,
                        "maximum": 60,
                    },
                },
                "required": ["node_id", "repo_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )


def register_markdown_tools(registry: ToolRegistry) -> None:
    """Register markdown write tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.markdown import write_markdown_handler

    # Register write_markdown tool
    # Policy: WRITE_REQUIREMENT - requires valid node + write target validation
    registry.register(
        ToolDefinition(
            name="write_markdown",
            description="Write markdown content to an approved write target. "
            "Validates that the target path is registered and the file extension is allowed. "
            "Writes atomically with SHA256 verification. "
            "Requires node, write_target, relative_path, and content parameters. "
            "Use mode='no_overwrite' to fail if the file already exists.",
            handler=write_markdown_handler,
            parameters={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node identifier (required)",
                    },
                    "write_target": {
                        "type": "string",
                        "description": "Write target identifier (required)",
                    },
                    "relative_path": {
                        "type": "string",
                        "description": "File path relative to write target root (required)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown content to write (required)",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Write mode: 'create_or_overwrite' (default) or 'no_overwrite'",
                        "enum": ["create_or_overwrite", "no_overwrite"],
                        "default": "create_or_overwrite",
                    },
                },
                "required": ["node", "write_target", "relative_path", "content"],
            },
            policy=WRITE_REQUIREMENT,
        )
    )


def register_all_tools(registry: ToolRegistry) -> None:
    """Register all hub tools.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    register_discovery_tools(registry)
    register_inspection_tools(registry)
    register_search_tools(registry)
    register_markdown_tools(registry)
    register_llm_tools(registry)
    register_context_tools(registry)
    register_cross_repo_tools(registry)
    register_relationship_tools(registry)
    register_architecture_tools(registry)
    register_observability_tools(registry)


def register_context_tools(registry: ToolRegistry) -> None:
    """Register context and indexing tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.context import (
        get_project_context_handler,
        record_issue_handler,
    )
    from src.hub.tools.indexing import index_repo_handler

    # Register index_repo tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="index_repo",
            description="Index repository content into Qdrant for semantic search. "
            "Reads all supported files from the repository, generates embeddings, "
            "and stores them in Qdrant with content-hash tracking for idempotent reindexing. "
            "Supports incremental mode (skip unchanged files) or full reindex. "
            "Requires node_id and repo_id for access control.",
            handler=index_repo_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository identifier to index (required)",
                    },
                    "node_id": {
                        "type": "string",
                        "description": "Node identifier (auto-detected from repo if not provided)",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Indexing mode: 'incremental' or 'full'",
                        "default": "incremental",
                        "enum": ["incremental", "full"],
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force full reindex even in incremental mode",
                        "default": False,
                    },
                },
                "required": ["repo_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register get_project_context tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="get_project_context",
            description="Search indexed repository content using semantic similarity. "
            "Performs natural language search over previously indexed files. "
            "Returns results with full provenance metadata (file path, repo, node, "
            "content hash, indexed timestamp, similarity score). "
            "Optionally filter by repo_id or node_id.",
            handler=get_project_context_handler,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (required)",
                    },
                    "repo_id": {
                        "type": "string",
                        "description": "Filter by specific repository (optional)",
                    },
                    "node_id": {
                        "type": "string",
                        "description": "Filter by specific node (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "score_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0 to 1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["query"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register record_issue tool
    # Policy: READ_REPO_REQUIREMENT - requires valid node + repo access
    registry.register(
        ToolDefinition(
            name="record_issue",
            description="Create and index a structured issue record. "
            "Creates an issue in SQLite and indexes it in Qdrant for semantic search. "
            "Validates that the repo_id is registered and approved. "
            "Supports issue status: open, in_progress, resolved, wontfix.",
            handler=record_issue_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository identifier (required)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title (required)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description (required)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Issue status",
                        "default": "open",
                        "enum": ["open", "in_progress", "resolved", "wontfix"],
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)",
                    },
                },
                "required": ["repo_id", "title", "description"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register build_context_bundle tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    from src.hub.tools.bundles import build_context_bundle_handler

    registry.register(
        ToolDefinition(
            name="build_context_bundle",
            description="Build a context bundle from indexed repository content. "
            "Creates a task-oriented, review, or research bundle by aggregating "
            "relevant files and issues. Returns the bundle with full provenance metadata. "
            "Requires repo_ids for access control.",
            handler=build_context_bundle_handler,
            parameters={
                "type": "object",
                "properties": {
                    "bundle_type": {
                        "type": "string",
                        "description": "Type of bundle: task, review, or research",
                        "enum": ["task", "review", "research"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Human-readable title for the bundle",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the bundle",
                    },
                    "repo_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of repository IDs to include in the bundle",
                    },
                    "task_query": {
                        "type": "string",
                        "description": "For task bundles: natural language query describing the task",
                    },
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "For review bundles: list of changed file paths",
                    },
                    "related_issue_query": {
                        "type": "string",
                        "description": "For review bundles: query for related issues",
                    },
                    "research_queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "For research bundles: list of research queries",
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to include",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "max_issues": {
                        "type": "integer",
                        "description": "Maximum number of issues to include",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["bundle_type", "title", "repo_ids"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register list_recurring_issues tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    from src.hub.tools.recurring import list_recurring_issues_handler

    registry.register(
        ToolDefinition(
            name="list_recurring_issues",
            description="Detect recurring issues across repositories. "
            "Aggregates issues by exact title match, semantic similarity, or metadata tags "
            "to identify repeated bugs, common blockers, or related issues. "
            "Returns grouped issues with provenance metadata.",
            handler=list_recurring_issues_handler,
            parameters={
                "type": "object",
                "properties": {
                    "aggregation_type": {
                        "type": "string",
                        "description": "Aggregation method: exact_title, semantic, or tag",
                        "default": "exact_title",
                        "enum": ["exact_title", "semantic", "tag"],
                    },
                    "repo_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of repository IDs to filter",
                    },
                    "min_count": {
                        "type": "integer",
                        "description": "Minimum issues required to form a recurring group",
                        "default": 2,
                        "minimum": 2,
                        "maximum": 100,
                    },
                    "score_threshold": {
                        "type": "number",
                        "description": "For semantic aggregation: minimum similarity score",
                        "default": 0.85,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "tag_key": {
                        "type": "string",
                        "description": "For tag aggregation: metadata key to group by",
                    },
                    "status_filter": {
                        "type": "string",
                        "description": "Filter by issue status",
                        "enum": ["open", "resolved", "wontfix"],
                    },
                },
                "required": [],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )


def register_llm_tools(registry: ToolRegistry) -> None:
    """Register LLM routing tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.embedding import chat_embeddings_handler
    from src.hub.tools.llm import chat_llm_handler
    from src.hub.tools.opencode import chat_opencode_handler

    # Register chat_llm tool
    # Policy: LLM_REQUIREMENT - requires valid LLM service access
    registry.register(
        ToolDefinition(
            name="chat_llm",
            description="Send a prompt to an approved LLM backend. "
            "Validates the service alias against the registry before routing. "
            "Returns the LLM response along with latency and token metadata. "
            "Supports various LLM backends including OpenCode, llama.cpp, and helper models.",
            handler=chat_llm_handler,
            parameters={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "LLM service identifier from the registry",
                    },
                    "service_name": {
                        "type": "string",
                        "description": "Human-readable service name (alternative to service_id)",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "User prompt to send to the LLM",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "default": 1000,
                        "maximum": 4096,
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 2.0,
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Optional system prompt to set context",
                        "default": None,
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation continuity",
                        "default": None,
                    },
                },
                "required": ["prompt"],
                "oneOf": [
                    {"required": ["service_id"]},
                    {"required": ["service_name"]},
                ],
            },
            policy=LLM_REQUIREMENT,
        )
    )

    # Register chat_opencode tool
    # Policy: LLM_REQUIREMENT - requires valid LLM service access
    registry.register(
        ToolDefinition(
            name="chat_opencode",
            description="Send a coding prompt to OpenCode with session support. "
            "Maintains conversation history across requests when session_id is provided. "
            "Supports working directory context for file operations. "
            "Returns OpenCode response including artifacts and tool executions.",
            handler=chat_opencode_handler,
            parameters={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "OpenCode service identifier from the registry",
                    },
                    "service_name": {
                        "type": "string",
                        "description": "Human-readable service name (alternative to service_id)",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "User prompt to send to OpenCode",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation continuity",
                        "default": None,
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Optional working directory for file operations",
                        "default": None,
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Optional system prompt to set context",
                        "default": None,
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "default": 4096,
                        "maximum": 8192,
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 2.0,
                    },
                    "include_history": {
                        "type": "boolean",
                        "description": "Whether to include conversation history",
                        "default": True,
                    },
                },
                "required": ["prompt"],
                "oneOf": [
                    {"required": ["service_id"]},
                    {"required": ["service_name"]},
                ],
            },
            policy=LLM_REQUIREMENT,
        )
    )

    # Register chat_embeddings tool
    # Policy: LLM_REQUIREMENT - requires valid LLM service access
    registry.register(
        ToolDefinition(
            name="chat_embeddings",
            description="Generate embeddings for text using an approved embedding service. "
            "Supports single text or batch embedding requests. "
            "Validates service type is EMBEDDING before routing. "
            "Returns embeddings array, model, and token usage metadata.",
            handler=chat_embeddings_handler,
            parameters={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Embedding service identifier from the registry",
                    },
                    "service_name": {
                        "type": "string",
                        "description": "Human-readable service name (alternative to service_id)",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to generate embeddings for (single input)",
                    },
                    "texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Texts to generate embeddings for (batch input)",
                    },
                    "encoding_format": {
                        "type": "string",
                        "description": "Encoding format: float, base64, or int8",
                        "default": "float",
                    },
                },
                "allOf": [
                    {
                        "oneOf": [
                            {"required": ["service_id"]},
                            {"required": ["service_name"]},
                        ],
                    },
                    {
                        "oneOf": [
                            {"required": ["text"]},
                            {"required": ["texts"]},
                        ],
                    },
                ],
            },
            policy=LLM_REQUIREMENT,
        )
    )


def register_cross_repo_tools(registry: ToolRegistry) -> None:
    """Register cross-repo search and landscape tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.cross_repo import (
        get_project_landscape_handler,
        list_related_repos_handler,
        search_across_repos_handler,
    )

    # Register search_across_repos tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="search_across_repos",
            description="Search indexed content across multiple repositories. "
            "Performs semantic search over files in specified repos or all accessible repos. "
            "Returns results with per-repo metadata and full provenance (repo_id, node_id, path, score). "
            "Use repo_ids to limit search to specific repos, or omit for global search across all accessible repos.",
            handler=search_across_repos_handler,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (required)",
                    },
                    "repo_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of repository IDs to search. If omitted, searches all accessible repos",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "score_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0 to 1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                },
                "required": ["query"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register list_related_repos tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="list_related_repos",
            description="Find repositories related to a given repo based on shared content. "
            "Identifies repos that share similar files, issues, or bundles. "
            "Returns list of related repos with relationship metadata and overlap scores. "
            "Requires valid repo_id for access control.",
            handler=list_related_repos_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository ID to find relationships for (required)",
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Type of relationship: files, issues, or bundles",
                        "default": "files",
                        "enum": ["files", "issues", "bundles"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum related repos to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20,
                    },
                },
                "required": ["repo_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register get_project_landscape tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="get_project_landscape",
            description="Get an overview of all accessible repositories with their metadata. "
            "Returns file counts, issue counts, detected languages, and optional relationship data. "
            "Access control is applied - only returns info for repos the caller has access to.",
            handler=get_project_landscape_handler,
            parameters={
                "type": "object",
                "properties": {
                    "include_relationships": {
                        "type": "boolean",
                        "description": "Include relationship data between repos",
                        "default": False,
                    },
                },
                "required": [],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )


def register_relationship_tools(registry: ToolRegistry) -> None:
    """Register relationship management tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.relationships import (
        create_relationship_handler,
        delete_relationship_handler,
        get_repo_owner_handler,
        list_relationships_handler,
        set_repo_owner_handler,
    )

    # Register create_relationship tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access for both source and target
    registry.register(
        ToolDefinition(
            name="create_relationship",
            description="Create an explicit relationship between two repositories. "
            "Creates a persistent relationship with provenance tracking. "
            "Validates that both source and target repos exist in the registry. "
            "Supported relationship types: depends_on, related_to, forks_from, contains, references, shared_dep.",
            handler=create_relationship_handler,
            parameters={
                "type": "object",
                "properties": {
                    "source_repo_id": {
                        "type": "string",
                        "description": "Source repository ID (required)",
                    },
                    "target_repo_id": {
                        "type": "string",
                        "description": "Target repository ID (required)",
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Type of relationship",
                        "enum": [
                            "depends_on",
                            "related_to",
                            "forks_from",
                            "contains",
                            "references",
                            "shared_dep",
                        ],
                    },
                    "description": {
                        "type": "string",
                        "description": "Human-readable relationship description",
                    },
                    "source_record": {
                        "type": "string",
                        "description": "Source of this relationship (e.g., 'git log', 'import scan', 'manual')",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score (0.0 to 1.0)",
                        "default": 1.0,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "bidirectional": {
                        "type": "boolean",
                        "description": "Whether relationship applies both ways",
                        "default": False,
                    },
                },
                "required": ["source_repo_id", "target_repo_id", "relationship_type"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register list_relationships tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="list_relationships",
            description="List explicit relationships between repositories. "
            "Can filter by repo_id, relationship_type, or list all relationships. "
            "Returns relationship metadata including provenance and confidence scores.",
            handler=list_relationships_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository ID to list relationships for. If omitted, lists all relationships.",
                    },
                    "include_incoming": {
                        "type": "boolean",
                        "description": "Include relationships where repo is target (only applies if repo_id provided)",
                        "default": True,
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Filter by relationship type",
                        "enum": [
                            "depends_on",
                            "related_to",
                            "forks_from",
                            "contains",
                            "references",
                            "shared_dep",
                        ],
                    },
                },
                "required": [],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register delete_relationship tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="delete_relationship",
            description="Delete an explicit repository relationship. "
            "Removes the relationship from the registry permanently.",
            handler=delete_relationship_handler,
            parameters={
                "type": "object",
                "properties": {
                    "relationship_id": {
                        "type": "string",
                        "description": "Relationship ID to delete (required)",
                    },
                },
                "required": ["relationship_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register set_repo_owner tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="set_repo_owner",
            description="Set or update owner information for a repository. "
            "Stores structured owner metadata including name, email, and role. "
            "Roles: maintainer, contributor, observer.",
            handler=set_repo_owner_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository ID (required)",
                    },
                    "owner_id": {
                        "type": "string",
                        "description": "Owner identifier (required)",
                    },
                    "name": {
                        "type": "string",
                        "description": "Owner name (required)",
                    },
                    "email": {
                        "type": "string",
                        "description": "Owner email",
                    },
                    "role": {
                        "type": "string",
                        "description": "Owner role",
                        "enum": ["maintainer", "contributor", "observer"],
                        "default": "maintainer",
                    },
                },
                "required": ["repo_id", "owner_id", "name"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register get_repo_owner tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="get_repo_owner",
            description="Get owner information for a repository. "
            "Returns the owner metadata including name, email, and role.",
            handler=get_repo_owner_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository ID (required)",
                    },
                },
                "required": ["repo_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )


def register_architecture_tools(registry: ToolRegistry) -> None:
    """Register architecture and landscape tools with the tool registry.

    Args:
        registry: ToolRegistry instance to register tools with.
    """
    from src.hub.tool_router import ToolDefinition
    from src.hub.tools.architecture import (
        get_architecture_map_handler,
        get_repo_architecture_handler,
    )

    # Register get_architecture_map tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="get_architecture_map",
            description="Generate a complete architecture map of accessible repositories. "
            "Returns architecture nodes (repos) with language distribution, file counts, "
            "and owner metadata. Optionally includes explicit relationships as edges. "
            "All data includes source citations for provenance. "
            "Use repo_ids to limit to specific repos, or omit for all accessible repos.",
            handler=get_architecture_map_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of repository IDs to include. If omitted, includes all accessible repos",
                    },
                    "include_relationships": {
                        "type": "boolean",
                        "description": "Include explicit relationships as edges",
                        "default": True,
                    },
                    "include_inferred": {
                        "type": "boolean",
                        "description": "Include inferred relationships (future feature)",
                        "default": True,
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth for dependency traversal (future)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": [],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )

    # Register get_repo_architecture tool
    # Policy: READ_REPO_REQUIREMENT - requires valid repo access
    registry.register(
        ToolDefinition(
            name="get_repo_architecture",
            description="Get architecture summary for a single repository. "
            "Returns language distribution, file counts, issue counts, owner metadata, "
            "and optional dependency information. Includes source citations for all data. "
            "Requires valid repo_id for access control.",
            handler=get_repo_architecture_handler,
            parameters={
                "type": "object",
                "properties": {
                    "repo_id": {
                        "type": "string",
                        "description": "Repository ID to get architecture for (required)",
                    },
                    "include_dependencies": {
                        "type": "boolean",
                        "description": "Include dependency information (future)",
                        "default": False,
                    },
                },
                "required": ["repo_id"],
            },
            policy=READ_REPO_REQUIREMENT,
        )
    )
