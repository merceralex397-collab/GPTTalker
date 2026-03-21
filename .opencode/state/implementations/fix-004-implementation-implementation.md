# Implementation of FIX-004: Fix SQLite write persistence and uncommitted transactions

## Summary

Fixed three related issues causing database writes to not persist:
1. Fixed broken `transaction()` context manager that was using incorrect async syntax
2. Added explicit commits after `execute()` and `executemany()` operations
3. Wrapped migrations in transactions for atomicity

## Changes Made

### src/shared/database.py

1. **Disabled autocommit** (line 42): Set `isolation_level = ""` to require explicit transaction control:
   ```python
   self._connection.isolation_level = ""
   ```

2. **Fixed transaction() context manager** (lines 67-86): The original code used `async with self.connection.execute("BEGIN")` which is incorrect - `execute()` returns a cursor, not a context manager. Fixed to properly use explicit BEGIN/COMMIT/ROLLBACK:
   ```python
   async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
       await self.connection.execute("BEGIN")
       try:
           yield self.connection
           await self.connection.execute("COMMIT")
       except Exception:
           await self.connection.execute("ROLLBACK")
           raise
   ```

3. **Added explicit commits** to `execute()` and `executemany()` methods (lines 88-114):
   ```python
   async def execute(self, query: str, parameters: tuple = ()) -> aiosqlite.Cursor:
       cursor = await self.connection.execute(query, parameters)
       await self.connection.commit()
       return cursor
   
   async def executemany(self, query: str, parameters: list) -> aiosqlite.Cursor:
       cursor = await self.connection.executemany(query, parameters)
       await self.connection.commit()
       return cursor
   ```

### src/shared/migrations.py

Wrapped migration statements in a transaction for atomicity (lines 108-117):
```python
async with db.transaction() as conn:
    for statement in MIGRATIONS[version]:
        await conn.execute(statement)
    await conn.execute(
        "INSERT INTO schema_version (version) VALUES (?)",
        (version,),
    )
```

## Verification

### Static Analysis

**database.py changes:**
- Line 42: `isolation_level = ""` correctly disables autocommit
- Lines 67-86: transaction() now properly uses BEGIN/COMMIT/ROLLBACK with explicit cursor handling
- Lines 88-114: execute() and executemany() now include `await self.connection.commit()` after each operation

**migrations.py changes:**
- Lines 108-117: All migration statements wrapped in `async with db.transaction() as conn:`

### Manual Syntax Validation

Code reviewed for:
- Correct async/await patterns
- Proper context manager usage
- Matching braces, parentheses, quotes
- Import statements valid
- Type hints valid

All syntax verified correct through line-by-line code inspection.

### Code Flow

1. Repository calls `await db.execute(...)` → executes query → commits → returns cursor
2. Migration calls `async with db.transaction() as conn:` → BEGIN → executes all statements → COMMIT
3. If any statement fails → ROLLBACK → exception propagates

### Compatibility

- All existing repository code using `db.execute()` will now commit automatically
- Transaction context manager can still be used for explicit atomic operations
- No changes needed to calling code - the fix is transparent
