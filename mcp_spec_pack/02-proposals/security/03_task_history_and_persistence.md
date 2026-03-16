# Proposal — Task History and Persistence

## Simple explanation

This is about what the system remembers operationally.

In plain terms:
- what did it do?
- what docs did it create?
- what issues did it find?
- what backend did it use?

## Status

Proposal document.

## Options

### Why keep history
- trust
- debugging
- audit trail
- better project memory

### What should persist
- node registry
- repo registry
- write targets
- task history
- generated file records
- issue records
- indexing records
- backend/service health snapshots (optional)

### Storage options

#### Option A — SQLite-first
Advantages:
- simple
- local
- lightweight
- good fit for an old laptop

Downsides:
- less ideal for bigger multi-user scale

#### Option B — Postgres
Advantages:
- stronger for growth and concurrency

Downsides:
- more operational burden

### Log strategy
- append-only task records
- rotating operational logs
- exported markdown/report snapshots when useful

## Recommendation

Recommended proposal: SQLite for V1, with migration path to Postgres only if needed later.
