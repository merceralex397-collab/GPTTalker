    # SETUP-003: Async SQLite persistence and migration baseline

    ## Summary

    Define the async SQLite layer, migration strategy, and shared persistence helpers for registries, history, and issue tracking.

    ## Wave

    0

    ## Lane

    storage

    ## Parallel Safety

    - parallel_safe: false
    - overlap_risk: medium

    ## Stage

    planning

    ## Status

    todo

    ## Depends On

    SETUP-001

    ## Acceptance Criteria

    - [ ] SQLite access pattern uses `aiosqlite`
- [ ] Initial runtime tables are identified
- [ ] Migration approach is explicit and reusable

    ## Decision Blockers

    None

    ## Artifacts

    - None yet

    ## Notes
