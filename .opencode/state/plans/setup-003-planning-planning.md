# SETUP-003: Async SQLite Persistence and Migration Baseline

## 1. Scope

This ticket establishes the foundational async SQLite layer for GPTTalker, providing:
- Async connection management using `aiosqlite`
- Complete table schemas for all runtime registries and history
- A reusable migration system with version tracking
- Shared persistence helpers (CRUD operations) for each table

## 2. Files and Systems Affected

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `src/shared/database.py` | Async SQLite connection manager with connection pooling |
| `src/shared/migrations.py` | Migration system with version tracking and auto-run |
| `src/shared/tables.py` | Table schema definitions and DDL |
| `src/shared/repositories/__init__.py` | Repository package init |
| `src/shared/repositories/nodes.py` | CRUD for nodes table |
| `src/shared/repositories/repos.py` | CRUD for repos table |
| `src/shared/repositories/write_targets.py` | CRUD for write_targets table |
| `src/shared/repositories/llm_services.py` | CRUD for llm_services table |
| `src/shared/repositories/tasks.py` | CRUD for tasks table |
| `src/shared/repositories/issues.py` | CRUD for issues table |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `pyproject.toml` | Add `aiosqlite` dependency |
| `src/shared/config.py` | Add database path configuration |
| `src/shared/__init__.py` | Export database and repository components |

### Dependencies
- `aiosqlite` - async SQLite driver (add to pyproject.toml)

## 3. Implementation Steps

### Step 1: Update Dependencies
Add `aiosqlite` to `pyproject.toml`:
```toml
dependencies = [
    ...
    "aiosqlite>=0.19.0",
]
```

### Step 2: Extend Config for Database
Add database configuration to `src/shared/config.py`:
```python
class SharedConfig(BaseSettings):
    ...
    # Database settings
    database_path: str = Field(
        "data/gpttalker.db",
        description="Path to SQLite database file"
    )
```

### Step 3: Create Table Schemas (`src/shared/tables.py`)
Define all table DDL with proper constraints:

```python
# Schema versions tracking
SCHEMA_VERSION = 1

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

# Indexes for performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_repos_node_id ON repos(node_id);",
    "CREATE INDEX IF NOT EXISTS idx_write_targets_repo_id ON write_targets(repo_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_trace_id ON tasks(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_issues_repo_id ON issues(repo_id);",
    "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);",
]
```

### Step 4: Create Connection Manager (`src/shared/database.py`)

```python
"""Async SQLite connection management."""

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from .config import SharedConfig, get_shared_config
from .logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages async SQLite connections for GPTTalker."""
    
    def __init__(self, config: SharedConfig | None = None):
        self._config = config or get_shared_config()
        self._db_path = self._config.database_path
        self._connection: aiosqlite.Connection | None = None
    
    async def initialize(self) -> None:
        """Initialize database connection and run migrations."""
        # Ensure directory exists
        db_path = Path(self._db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row
        
        logger.info("database_initialized", db_path=str(self._db_path))
    
    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("database_closed")
    
    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the current connection."""
        if not self._connection:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._connection
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Context manager for database transactions."""
        async with self.connection.execute("BEGIN") as cursor:
            try:
                yield cursor
                await cursor.execute("COMMIT")
            except Exception:
                await cursor.execute("ROLLBACK")
                raise
    
    async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query and return cursor."""
        return await self.connection.execute(query, parameters)
    
    async def executemany(self, query: str, parameters: list) -> aiosqlite.Cursor:
        """Execute a query with multiple parameter sets."""
        return await self.connection.executemany(query, parameters)
    
    async def fetchone(self, query: str, parameters: tuple = ()) -> aiosqlite.Row | None:
        """Execute query and fetch one result."""
        async with self.connection.execute(query, parameters) as cursor:
            return await cursor.fetchone()
    
    async def fetchall(self, query: str, parameters: tuple = ()) -> list[aiosqlite.Row]:
        """Execute query and fetch all results."""
        async with self.connection.execute(query, parameters) as cursor:
            return await cursor.fetchall()


# Global instance
_db_manager: DatabaseManager | None = None


def get_db_manager(config: SharedConfig | None = None) -> DatabaseManager:
    """Get or create the global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config)
    return _db_manager


async def initialize_database(config: SharedConfig | None = None) -> DatabaseManager:
    """Initialize the database and run migrations."""
    manager = get_db_manager(config)
    await manager.initialize()
    
    from .migrations import run_migrations
    await run_migrations(manager)
    
    return manager
```

### Step 5: Create Migration System (`src/shared/migrations.py`)

```python
"""Migration system for database schema versioning."""

from .tables import (
    CREATE_SCHEMA_VERSION_TABLE,
    CREATE_NODES_TABLE,
    CREATE_REPOS_TABLE,
    CREATE_WRITE_TARGETS_TABLE,
    CREATE_LLM_SERVICES_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_ISSUES_TABLE,
    CREATE_INDEXES,
    SCHEMA_VERSION,
)
from .logging import get_logger

logger = get_logger(__name__)


# Migration definitions - each entry maps version to upgrade function
MIGRATIONS: dict[int, list[str]] = {
    1: [
        CREATE_SCHEMA_VERSION_TABLE,
        CREATE_NODES_TABLE,
        CREATE_REPOS_TABLE,
        CREATE_WRITE_TARGETS_TABLE,
        CREATE_LLM_SERVICES_TABLE,
        CREATE_TASKS_TABLE,
        CREATE_ISSUES_TABLE,
        *CREATE_INDEXES,
    ],
    # Future migrations:
    # 2: [...],
}


async def get_schema_version(db) -> int:
    """Get the current schema version from database."""
    try:
        row = await db.fetchone("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        return row["version"] if row else 0
    except Exception:
        return 0


async def run_migrations(db) -> None:
    """Run all pending migrations."""
    current_version = await get_schema_version(db)
    
    if current_version >= SCHEMA_VERSION:
        logger.info("database_up_to_date", version=current_version)
        return
    
    logger.info("running_migrations", from_version=current_version, to_version=SCHEMA_VERSION)
    
    for version in range(current_version + 1, SCHEMA_VERSION + 1):
        if version not in MIGRATIONS:
            logger.warning("migration_not_found", version=version)
            continue
        
        logger.info("applying_migration", version=version)
        
        for statement in MIGRATIONS[version]:
            await db.execute(statement)
        
        # Record migration
        await db.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (version,)
        )
        
        logger.info("migration_applied", version=version)
    
    logger.info("migrations_complete", final_version=SCHEMA_VERSION)
```

### Step 6: Create Repository Classes

Each repository follows this pattern (example for nodes):

```python
# src/shared/repositories/nodes.py
"""Node repository for CRUD operations."""

from datetime import datetime
from typing import Any

from ..database import DatabaseManager
from ..logging import get_logger
from ..models import NodeInfo, NodeStatus

logger = get_logger(__name__)


class NodeRepository:
    """Repository for node registry operations."""
    
    def __init__(self, db: DatabaseManager):
        self._db = db
    
    async def create(self, node: NodeInfo) -> NodeInfo:
        """Create a new node."""
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            """INSERT INTO nodes (node_id, name, hostname, status, last_seen, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                node.node_id,
                node.name,
                node.hostname,
                node.status.value,
                node.last_seen.isoformat() if node.last_seen else None,
                now,
                "{}",
            ),
        )
        logger.info("node_created", node_id=node.node_id)
        return node
    
    async def get(self, node_id: str) -> NodeInfo | None:
        """Get a node by ID."""
        row = await self._db.fetchone(
            "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
        )
        if not row:
            return None
        return self._row_to_node(row)
    
    async def list_all(self) -> list[NodeInfo]:
        """List all nodes."""
        rows = await self._db.fetchall("SELECT * FROM nodes ORDER BY created_at DESC")
        return [self._row_to_node(row) for row in rows]
    
    async def update(self, node: NodeInfo) -> NodeInfo | None:
        """Update an existing node."""
        await self._db.execute(
            """UPDATE nodes SET name = ?, hostname = ?, status = ?, last_seen = ?
               WHERE node_id = ?""",
            (
                node.name,
                node.hostname,
                node.status.value,
                node.last_seen.isoformat() if node.last_seen else None,
                node.node_id,
            ),
        )
        logger.info("node_updated", node_id=node.node_id)
        return node
    
    async def delete(self, node_id: str) -> bool:
        """Delete a node."""
        cursor = await self._db.execute(
            "DELETE FROM nodes WHERE node_id = ?", (node_id,)
        )
        logger.info("node_deleted", node_id=node_id)
        return cursor.rowcount > 0
    
    async def update_status(self, node_id: str, status: NodeStatus) -> None:
        """Update node status."""
        await self._db.execute(
            "UPDATE nodes SET status = ?, last_seen = ? WHERE node_id = ?",
            (status.value, datetime.utcnow().isoformat(), node_id),
        )
    
    def _row_to_node(self, row) -> NodeInfo:
        """Convert database row to NodeInfo."""
        return NodeInfo(
            node_id=row["node_id"],
            name=row["name"],
            hostname=row["hostname"],
            status=NodeStatus(row["status"]),
            last_seen=datetime.fromisoformat(row["last_seen"]) if row["last_seen"] else None,
        )
```

Repeat similar patterns for:
- `repos.py` - RepoRepository
- `write_targets.py` - WriteTargetRepository  
- `llm_services.py` - LLMServiceRepository
- `tasks.py` - TaskRepository
- `issues.py` - IssueRepository

### Step 7: Update Exports

Add exports to `src/shared/__init__.py`:
```python
from .database import DatabaseManager, get_db_manager, initialize_database
from .migrations import run_migrations
from .repositories import (
    NodeRepository,
    RepoRepository,
    WriteTargetRepository,
    LLMServiceRepository,
    TaskRepository,
    IssueRepository,
)
```

## 4. Validation Plan

### Validation Commands

```bash
# 1. Check aiosqlite is installed
python -c "import aiosqlite; print(aiosqlite.__version__)"

# 2. Run database initialization test
python -c "
import asyncio
from src.shared.database import initialize_database

async def test():
    db = await initialize_database()
    print('Database initialized successfully')
    
    # Check schema version
    row = await db.fetchone('SELECT version FROM schema_version')
    print(f'Schema version: {row[0]}')
    
    # List tables
    rows = await db.fetchall(\"SELECT name FROM sqlite_master WHERE type='table'\")
    print(f'Tables: {[r[0] for r in rows]}')
    
    await db.close()

asyncio.run(test())
"

# 3. Run CRUD tests for each repository
python -c "
import asyncio
from src.shared.database import initialize_database
from src.shared.repositories import NodeRepository
from src.shared.models import NodeInfo, NodeStatus

async def test():
    db = await initialize_database()
    repo = NodeRepository(db)
    
    # Create
    node = NodeInfo(
        node_id='test-node',
        name='Test Node',
        hostname='test.local',
        status=NodeStatus.HEALTHY
    )
    await repo.create(node)
    
    # Read
    fetched = await repo.get('test-node')
    print(f'Created: {fetched}')
    
    # Update
    fetched.status = NodeStatus.UNHEALTHY
    await repo.update(fetched)
    
    # Delete
    await repo.delete('test-node')
    print('CRUD test passed')
    
    await db.close()

asyncio.run(test())
"

# 4. Run linter
ruff check src/shared/database.py src/shared/migrations.py src/shared/tables.py src/shared/repositories/

# 5. Run type checker  
mypy src/shared/database.py src/shared/migrations.py src/shared/repositories/
```

### Expected Output
- All tables created with correct schemas
- Schema version recorded as 1
- CRUD operations work correctly
- No lint or type errors

## 5. Risks and Assumptions

### Risks
- **Concurrent access**: Single connection may not handle high concurrency - consider connection pool if needed later
- **Large datasets**: Queries without indexes may be slow - indexes are included but may need tuning
- **Migration safety**: Down migrations not implemented - only forward migrations for V1

### Assumptions
- SQLite file-based storage is acceptable (not in-memory)
- Single-writer pattern is sufficient for hub workload
- No multi-process SQLite access (node agent uses separate DB or shares via hub)
- JSON metadata fields can be stored as TEXT with JSON serialization

## 6. Blockers and Required User Decisions

### Blockers
None - all acceptance criteria can be met with the proposed implementation.

### Decisions Not Required
- Connection pooling: Single connection with transaction context is sufficient for V1
- Migration rollback: Not required for initial release; can add if needed later
- Database location: Defaults to `data/gpttalker.db` (configurable via env)
