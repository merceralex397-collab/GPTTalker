# SETUP-003: SQLite database layer

## Summary

Design and implement the SQLite persistence layer for the GPTTalker hub. Define the schema covering all core entities: nodes, repos, write_targets, llm_services, tasks, generated_docs, issues, and indexing_status. Provide async database access via aiosqlite with a clean repository pattern, plus a migration/initialization script that creates tables on first run.

## Stage

planning

## Status

todo

## Depends On

- SETUP-001

## Acceptance Criteria

- [ ] Schema SQL file defines all tables with appropriate constraints and indexes
- [ ] Tables: nodes, repos, write_targets, llm_services, tasks, generated_docs, issues, indexing_status
- [ ] Async database helper module wraps aiosqlite with context managers
- [ ] Database init function creates all tables idempotently (IF NOT EXISTS)
- [ ] Migration script or versioning mechanism for future schema changes
- [ ] Foreign key enforcement is enabled
- [ ] All datetime columns use ISO 8601 format
- [ ] Unit tests verify table creation and basic CRUD

## Artifacts

- None yet

## Notes

- aiosqlite wraps sqlite3 in a thread — acceptable for hub workloads
- Consider WAL mode for concurrent reads during indexing
- Schema should support soft-delete (is_active flag) for nodes/repos
- Keep migration simple for V1 — full Alembic-style migrations are overkill
