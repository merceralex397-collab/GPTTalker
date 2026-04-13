# Implementation Plan for FIX-018

## Bug Summary

Migration 1 in `src/shared/migrations.py` includes `*CREATE_INDEXES` which contains indexes for tables created in later migrations:
- Lines 177-179 of `CREATE_INDEXES` reference `relationships` table (created in migration 3)
- Lines 181-186 reference `audit_log` and `generated_docs` tables (created in migration 4)

This causes `sqlite3.OperationalError: no such table: relationships` on fresh databases.

## Root Cause

The `CREATE_INDEXES` list in `tables.py` is a flat collection of all indexes across all migrations. When migration 1 expands `*CREATE_INDEXES`, it tries to create indexes on tables that don't exist yet.

## Fix Strategy

Split `CREATE_INDEXES` into three separate lists aligned with the migration that creates each table:
- `CREATE_INDEXES_MIGRATION_1` - indexes for tables created in migration 1 (repos, write_targets, tasks, issues)
- `CREATE_INDEXES_MIGRATION_3` - indexes for relationships table  
- `CREATE_INDEXES_MIGRATION_4` - indexes for audit_log and generated_docs tables

## Files to Modify

### 1. `src/shared/tables.py`

Replace the single `CREATE_INDEXES` list (lines 168-187) with three separate lists:

```python
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
```

### 2. `src/shared/migrations.py`

Update the import to include the three new index lists:

```python
from .tables import (
    CREATE_AUDIT_LOG_TABLE,
    CREATE_GENERATED_DOCS_TABLE,
    CREATE_INDEXES_MIGRATION_1,
    CREATE_INDEXES_MIGRATION_3,
    CREATE_INDEXES_MIGRATION_4,
    CREATE_ISSUES_TABLE,
    CREATE_LLM_SERVICES_TABLE,
    CREATE_NODES_TABLE,
    CREATE_RELATIONSHIPS_TABLE,
    CREATE_REPO_OWNERS_TABLE,
    CREATE_REPOS_TABLE,
    CREATE_SCHEMA_VERSION_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_WRITE_TARGETS_TABLE,
    SCHEMA_VERSION,
)
```

Then update the MIGRATIONS dict:
- Migration 1: replace `*CREATE_INDEXES` with `*CREATE_INDEXES_MIGRATION_1`
- Migration 3: replace inline relationship index SQL with `*CREATE_INDEXES_MIGRATION_3`
- Migration 4: replace inline audit/generated_docs index SQL with `*CREATE_INDEXES_MIGRATION_4`

## Verification

Test with async wrapper since `run_migrations` is async:
```python
import asyncio
import sqlite3

async def test():
    from src.shared.database import DatabaseManager
    from src.shared.migrations import run_migrations
    
    db = DatabaseManager()
    db._connection = sqlite3.connect(':memory:')
    db._connection.row_factory = sqlite3.Row
    await run_migrations(db)
    print('OK')

asyncio.run(test())
```

Expected: exits 0 and prints OK without OperationalError.

## Acceptance Criteria

1. CREATE INDEX statements for tables created in migration 1 (repos, write_targets, tasks, issues) are in migration 1
2. CREATE INDEX statements for relationships table are in migration 3  
3. CREATE INDEX statements for audit_log and generated_docs tables are in migration 4
4. Fresh database initialization succeeds without OperationalError