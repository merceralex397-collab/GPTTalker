"""Migration system for database schema versioning."""

from .database import DatabaseManager
from .logging import get_logger
from .tables import (
    CREATE_AUDIT_LOG_TABLE,
    CREATE_GENERATED_DOCS_TABLE,
    CREATE_INDEXES,
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
    # Migration 2: Add health tracking columns to nodes table
    2: [
        "ALTER TABLE nodes ADD COLUMN health_status TEXT DEFAULT 'unknown';",
        "ALTER TABLE nodes ADD COLUMN health_latency_ms INTEGER;",
        "ALTER TABLE nodes ADD COLUMN health_error TEXT;",
        "ALTER TABLE nodes ADD COLUMN health_check_count INTEGER DEFAULT 0;",
        "ALTER TABLE nodes ADD COLUMN consecutive_failures INTEGER DEFAULT 0;",
        "ALTER TABLE nodes ADD COLUMN last_health_check TEXT;",
        "ALTER TABLE nodes ADD COLUMN last_health_attempt TEXT;",
    ],
    # Migration 3: Add relationships and repo_owners tables
    3: [
        CREATE_RELATIONSHIPS_TABLE,
        CREATE_REPO_OWNERS_TABLE,
        "CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_repo_id);",
        "CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_repo_id);",
        "CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);",
    ],
    # Migration 4: Add generated_docs and audit_log tables (OBS-001)
    4: [
        CREATE_GENERATED_DOCS_TABLE,
        CREATE_AUDIT_LOG_TABLE,
        "CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_log(trace_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);",
        "CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);",
        "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_generated_docs_trace_id ON generated_docs(trace_id);",
        "CREATE INDEX IF NOT EXISTS idx_generated_docs_tool ON generated_docs(tool_name);",
    ],
}


async def get_schema_version(db: DatabaseManager) -> int:
    """Get the current schema version from database.

    Args:
        db: DatabaseManager instance.

    Returns:
        Current schema version, or 0 if no migrations have been applied.
    """
    try:
        row = await db.fetchone("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        return row["version"] if row else 0
    except Exception:
        return 0


async def run_migrations(db: DatabaseManager) -> None:
    """Run all pending migrations.

    Applies any migrations that have not yet been run based on the
    current schema version in the database.

    Args:
        db: DatabaseManager instance to run migrations on.
    """
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
            (version,),
        )

        logger.info("migration_applied", version=version)

    logger.info("migrations_complete", final_version=SCHEMA_VERSION)


async def get_db_version(db: DatabaseManager) -> int:
    """Get the current database schema version.

    This is an alias for get_schema_version for convenience.

    Args:
        db: DatabaseManager instance.

    Returns:
        Current schema version.
    """
    return await get_schema_version(db)
