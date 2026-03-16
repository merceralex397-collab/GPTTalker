    # WRITE-001: write_markdown with atomic scoped writes

    ## Summary

    Implement the markdown delivery path with approved write targets, extension allowlists, content hashing, and atomic writes.

    ## Wave

    2

    ## Lane

    markdown

    ## Parallel Safety

    - parallel_safe: true
    - overlap_risk: low

    ## Stage

    planning

    ## Status

    todo

    ## Depends On

    CORE-002, CORE-004, CORE-005, CORE-006

    ## Acceptance Criteria

    - [ ] Writes are restricted to approved targets
- [ ] Atomic write behavior is explicit
- [ ] Write responses include verification metadata

    ## Decision Blockers

    None

    ## Artifacts

    - None yet

    ## Notes
