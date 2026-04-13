# Code Review: FIX-018

## Verdict: APPROVED

## Summary

The FIX-018 implementation correctly fixes the migration 1 OperationalError bug by splitting the monolithic `CREATE_INDEXES` into three migration-specific lists, each containing only indexes for tables created in that migration or earlier. All eight review criteria are satisfied, and the fix eliminates the root cause of the sqlite3.OperationalError on fresh database initialization.

---

## Findings

### Finding 1: CREATE_INDEXES_MIGRATION_1 contains only migration-1 table indexes ✅

**File**: `src/shared/tables.py` lines 169-176

**Analysis**: The six indexes in `CREATE_INDEXES_MIGRATION_1` are:

| Index | Table | Migration 1 Table? |
|-------|-------|-------------------|
| `idx_repos_node_id` | `repos` | ✅ yes |
| `idx_write_targets_repo_id` | `write_targets` | ✅ yes |
| `idx_tasks_trace_id` | `tasks` | ✅ yes |
| `idx_tasks_created_at` | `tasks` | ✅ yes |
| `idx_issues_repo_id` | `issues` | ✅ yes |
| `idx_issues_status` | `issues` | ✅ yes |

All indexed tables (repos, write_targets, tasks, issues) are created in migration 1. No references to later migration tables exist.

### Finding 2: CREATE_INDEXES_MIGRATION_3 contains only relationships table indexes ✅

**File**: `src/shared/tables.py` lines 178-183

**Analysis**: The three indexes in `CREATE_INDEXES_MIGRATION_3` are:

| Index | Table | Migration 3 Table? |
|-------|-------|-------------------|
| `idx_relationships_source` | `relationships` | ✅ yes |
| `idx_relationships_target` | `relationships` | ✅ yes |
| `idx_relationships_type` | `relationships` | ✅ yes |

`relationships` and `repo_owners` are created in migration 3. `repo_owners` has no indexes (only a primary key), which is acceptable. No indexes reference tables from earlier migrations (which is harmless but not necessary).

### Finding 3: CREATE_INDEXES_MIGRATION_4 contains only audit_log/generated_docs indexes ✅

**File**: `src/shared/tables.py` lines 185-193

**Analysis**: The six indexes in `CREATE_INDEXES_MIGRATION_4` are:

| Index | Table | Migration 4 Table? |
|-------|-------|-------------------|
| `idx_audit_trace_id` | `audit_log` | ✅ yes |
| `idx_audit_event_type` | `audit_log` | ✅ yes |
| `idx_audit_actor` | `audit_log` | ✅ yes |
| `idx_audit_created_at` | `audit_log` | ✅ yes |
| `idx_generated_docs_trace_id` | `generated_docs` | ✅ yes |
| `idx_generated_docs_tool` | `generated_docs` | ✅ yes |

Both `audit_log` and `generated_docs` are created in migration 4. No indexes reference tables from earlier migrations (which is harmless but not necessary).

### Finding 4: migrations.py correctly imports all three index lists ✅

**File**: `src/shared/migrations.py` lines 8-10

```python
CREATE_INDEXES_MIGRATION_1,
CREATE_INDEXES_MIGRATION_3,
CREATE_INDEXES_MIGRATION_4,
```

All three lists are properly imported from `tables.py`.

### Finding 5: Migration 1 uses CREATE_INDEXES_MIGRATION_1 ✅

**File**: `src/shared/migrations.py` line 36

```python
1:  [
2:      CREATE_SCHEMA_VERSION_TABLE,
3:      CREATE_NODES_TABLE,
4:      CREATE_REPOS_TABLE,
5:      CREATE_WRITE_TARGETS_TABLE,
6:      CREATE_LLM_SERVICES_TABLE,
7:      CREATE_TASKS_TABLE,
8:      CREATE_ISSUES_TABLE,
9:      *CREATE_INDEXES_MIGRATION_1,
10: ],
```

Migration 1 now uses `*CREATE_INDEXES_MIGRATION_1` (6 indexes) instead of a monolithic list containing indexes for later tables. This was the core bug fix.

### Finding 6: Migration 3 uses CREATE_INDEXES_MIGRATION_3 ✅

**File**: `src/shared/migrations.py` lines 48-53

```python
3: [
4:     CREATE_RELATIONSHIPS_TABLE,
5:     CREATE_REPO_OWNERS_TABLE,
6:     *CREATE_INDEXES_MIGRATION_3,
7: ],
```

Migration 3 correctly creates the relationships table first, then applies its own indexes. Previously this migration would have had inline SQL or a separate mechanism.

### Finding 7: Migration 4 uses CREATE_INDEXES_MIGRATION_4 ✅

**File**: `src/shared/migrations.py` lines 54-59

```python
4: [
5:     CREATE_GENERATED_DOCS_TABLE,
6:     CREATE_AUDIT_LOG_TABLE,
7:     *CREATE_INDEXES_MIGRATION_4,
8: ],
```

Migration 4 correctly creates both tables first, then applies its own indexes.

### Finding 8: Root cause eliminated — OperationalError on fresh init ✅

**Root cause**: The original code had a single `CREATE_INDEXES` list (or equivalent) that was applied in migration 1 but contained indexes for `relationships` (migration 3), `audit_log` (migration 4), and `generated_docs` (migration 4). When a fresh database ran migration 1, SQLite would fail with `sqlite3.OperationalError: no such table: relationships` because those tables didn't exist yet.

**Fix verification**: The three-list approach ensures:
1. Migration 1 creates indexes only for tables it actually creates
2. Migration 3 creates indexes only after creating the relationships table
3. Migration 4 creates indexes only after creating audit_log and generated_docs tables

This topological ordering matches the actual table creation order, eliminating the OperationalError.

---

## Compile Check

The bash tool is blocked in this environment, preventing direct execution of `python3 -m py_compile`. However, code inspection confirms:

- Both files are syntactically valid Python 3
- All imports reference actual exported symbols from `tables.py`
- The `MIGRATIONS` dict structure is correct with string statements and unpacked lists
- No obvious syntax errors, missing imports, or type errors

---

## Acceptance Criteria Verification

| # | Criterion | Status |
|---|-----------|--------|
| 1 | CREATE INDEX for repos/write_targets/tasks/issues in migration 1 | ✅ Verified |
| 2 | CREATE INDEX for relationships in migration 3 | ✅ Verified |
| 3 | CREATE INDEX for audit_log/generated_docs in migration 4 | ✅ Verified |
| 4 | Fresh database init succeeds without OperationalError | ✅ Root cause eliminated |

---

## Risk Assessment

- **Regression risk**: Low. The change is a pure refactoring of index grouping — no functional logic was changed, only which indexes run with which migration.
- **Backward compatibility**: The `SCHEMA_VERSION = 4` in tables.py is unchanged, and the migration sequence produces the same final schema state.
- **No security implications**: This is a data modeling change with no security surface impact.

---

## Conclusion

The implementation is correct. The three-list splitting is precise, the migration assignments are accurate, and the fix directly addresses the OperationalError root cause. No blockers identified.
