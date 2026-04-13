"""Table schema definitions for GPTTalker SQLite database."""

# Schema version tracking
SCHEMA_VERSION = 4

# Schema version table - tracks applied migrations
CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Nodes table - tracks managed machines
CREATE_NODES_TABLE = """
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hostname TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unknown',
    last_seen TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);
"""

# Repositories table - tracks approved repos
CREATE_REPOS_TABLE = """
CREATE TABLE IF NOT EXISTS repos (
    repo_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    is_indexed INTEGER NOT NULL DEFAULT 0,
    indexed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);
"""

# Write targets table - scoped write permissions
CREATE_WRITE_TARGETS_TABLE = """
CREATE TABLE IF NOT EXISTS write_targets (
    target_id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    path TEXT NOT NULL,
    allowed_extensions TEXT NOT NULL DEFAULT '[" .md",".txt"]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);
"""

# LLM services table - registered LLM backends
CREATE_LLM_SERVICES_TABLE = """
CREATE TABLE IF NOT EXISTS llm_services (
    service_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    endpoint TEXT,
    api_key TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);
"""

# Tasks table - task history and audit
CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    trace_id TEXT,
    tool_name TEXT NOT NULL,
    caller TEXT NOT NULL,
    target_node TEXT,
    target_repo TEXT,
    outcome TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Issues table - known issue tracking
CREATE_ISSUES_TABLE = """
CREATE TABLE IF NOT EXISTS issues (
    issue_id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);
"""

# Relationships table - explicit repo relationships
CREATE_RELATIONSHIPS_TABLE = """
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id TEXT PRIMARY KEY,
    source_repo_id TEXT NOT NULL,
    target_repo_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    confidence REAL DEFAULT 1.0,
    bidirectional INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    source_record TEXT,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (source_repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (target_repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);
"""

# Repo owners table - structured ownership
CREATE_REPO_OWNERS_TABLE = """
CREATE TABLE IF NOT EXISTS repo_owners (
    repo_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'maintainer',
    added_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);
"""

# Generated docs table - track generated/delivered documents
CREATE_GENERATED_DOCS_TABLE = """
CREATE TABLE IF NOT EXISTS generated_docs (
    doc_id TEXT PRIMARY KEY,
    trace_id TEXT,
    tool_name TEXT NOT NULL,
    caller TEXT NOT NULL,
    target_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);
"""

# Audit log table - full audit trail with trace context
CREATE_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    trace_id TEXT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    duration_ms INTEGER,
    error TEXT,
    trace_context TEXT DEFAULT '{}',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Indexes for tables created in migration 1 (repos, write_targets, tasks, issues)
CREATE_INDEXES_MIGRATION_1 = [
    "CREATE INDEX IF NOT EXISTS idx_repos_node_id ON repos(node_id);",
    "CREATE INDEX IF NOT EXISTS idx_write_targets_repo_id ON write_targets(repo_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_trace_id ON tasks(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_issues_repo_id ON issues(repo_id);",
    "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);",
]

# Indexes for relationships table (created in migration 3)
CREATE_INDEXES_MIGRATION_3 = [
    "CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_repo_id);",
    "CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_repo_id);",
    "CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);",
]

# Indexes for audit_log and generated_docs tables (created in migration 4)
CREATE_INDEXES_MIGRATION_4 = [
    "CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_log(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);",
    "CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);",
    "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_generated_docs_trace_id ON generated_docs(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_generated_docs_tool ON generated_docs(tool_name);",
]

# All tables list for reference
ALL_TABLES = [
    CREATE_SCHEMA_VERSION_TABLE,
    CREATE_NODES_TABLE,
    CREATE_REPOS_TABLE,
    CREATE_WRITE_TARGETS_TABLE,
    CREATE_LLM_SERVICES_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_ISSUES_TABLE,
]
