# Implementation Plan: FIX-004 - Fix SQLite write persistence and uncommitted transactions

## Ticket Summary

DatabaseManager.execute()/executemany() never commit. Migrations and repositories perform DDL/DML outside transaction() context manager, causing silent data loss on connection close.

## Issue Analysis

### Issue 1: execute()/executemany() don't commit

**Location**: `src/shared/database.py`, lines 84-106

The `execute()` and `executemany()` methods directly call `self.connection.execute()` and `self.connection.executemany()` without any transaction handling. Changes may not persist if autocommit is not properly enabled.

### Issue 2: transaction() context manager is broken

**Location**: `src/shared/database.py`, lines 64-82

The transaction context manager has a bug at line 76:
```python
async with self.connection.execute("BEGIN") as cursor:
```
This is incorrect - `execute()` returns a cursor, not an async context manager. The correct pattern should use `await` without `async with`.

### Issue 3: Repositories and migrations use execute() directly

All repositories and migrations call `db.execute()` directly without wrapping in a transaction. If autocommit is disabled, changes won't persist.

## Proposed Fix

1. **Fix the transaction() context manager**:
   - Change from `async with self.connection.execute("BEGIN")` to proper transaction handling
   - Use `await` instead of `async with` for BEGIN

2. **Add explicit commit after execute()/executemany()**:
   - Call `await self.connection.commit()` after execute() and executemany()
   - Or ensure proper isolation_level for autocommit

3. **Ensure migrations are wrapped in transaction**:
   - Wrap each migration version's statements in a transaction
   - If any statement fails, rollback the entire version

4. **Add test for write-close-reopen-read roundtrip**:
   - Create a test that writes data, closes the connection, reopens, and verifies data persists

## Implementation Steps

1. **Fix transaction() context manager** in database.py
2. **Add commit after execute()/executemany()** or ensure proper autocommit
3. **Wrap migrations in transaction** in migrations.py
4. **Verify** write-close-reopen-read roundtrip works

## Acceptance Criteria

- [ ] All DDL operations persist across connection close/reopen
- [ ] All DML operations persist correctly
- [ ] Migrations remain durable after application
- [ ] Test verifies write-close-reopen-read roundtrip

## Risk Assessment

- **Risk level**: Medium
- **Impact**: Data persistence issue affecting all database operations
- **Mitigation**: Careful transaction handling, testing

## Dependencies

None
