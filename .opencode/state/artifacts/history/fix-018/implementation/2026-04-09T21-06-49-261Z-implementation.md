# Implementation of FIX-018: Fix migration 1 CREATE INDEXES referencing tables from later migrations

## Summary

Fixed the bug where Migration 1 in `src/shared/migrations.py` included `*CREATE_INDEXES` which contained indexes for tables created in later migrations (relationships in migration 3, audit_log/generated_docs in migration 4). This caused `sqlite3.OperationalError: no such table: relationships` on fresh databases.

## Changes Made

### 1. `src/shared/tables.py` (lines 168-198)

**Before:** Single flat `CREATE_INDEXES` list containing all indexes including those for migrations 3 and 4.

**After:** Split into three separate lists aligned with the migration that creates each table:

- `CREATE_INDEXES_MIGRATION_1` - indexes for repos, write_targets, tasks, issues tables (migration 1)
- `CREATE_INDEXES_MIGRATION_3` - indexes for relationships table (migration 3)
- `CREATE_INDEXES_MIGRATION_4` - indexes for audit_log and generated_docs tables (migration 4)

### 2. `src/shared/migrations.py` (lines 5-21, 28-59)

**Import changes:** Replaced `CREATE_INDEXES` with three separate imports:
- `CREATE_INDEXES_MIGRATION_1`
- `CREATE_INDEXES_MIGRATION_3`
- `CREATE_INDEXES_MIGRATION_4`

**Migration 1:** Changed `*CREATE_INDEXES` to `*CREATE_INDEXES_MIGRATION_1`

**Migration 3:** Replaced inline relationship index SQL with `*CREATE_INDEXES_MIGRATION_3`

**Migration 4:** Replaced inline audit/generated_docs index SQL with `*CREATE_INDEXES_MIGRATION_4`

## Validation Evidence

### Syntax Check
```
$ python3 -m py_compile src/shared/tables.py src/shared/migrations.py && echo "SYNTAX OK"
SYNTAX OK
```

### Import Check
```
$ python3 -c "from src.shared.migrations import MIGRATIONS; print('IMPORT OK')"
IMPORT OK
```

### Fresh Database Migration Test
```
$ python3 -c "
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
"
OK
```

## Acceptance Criteria Verification

| Criterion | Status |
|---|---|
| CREATE INDEX statements for tables created in migration 1 (repos, write_targets, tasks, issues) are in migration 1 | ✅ Verified - `CREATE_INDEXES_MIGRATION_1` used in migration 1 |
| CREATE INDEX statements for relationships table are in migration 3 | ✅ Verified - `CREATE_INDEXES_MIGRATION_3` used in migration 3 |
| CREATE INDEX statements for audit_log and generated_docs tables are in migration 4 | ✅ Verified - `CREATE_INDEXES_MIGRATION_4` used in migration 4 |
| Fresh database initialization succeeds without OperationalError | ✅ Verified - test passed with "OK" output |

## Files Modified

1. `src/shared/tables.py` - Split `CREATE_INDEXES` into three migration-specific lists
2. `src/shared/migrations.py` - Updated imports and migration definitions to use correct index lists
