    # SCHED-001: Task classification and routing policy

    ## Summary

    Define how GPTTalker classifies task types and selects between approved LLM and execution backends.

    ## Wave

    4

    ## Lane

    scheduler

    ## Parallel Safety

    - parallel_safe: true
    - overlap_risk: low

    ## Stage

    planning

    ## Status

    todo

    ## Depends On

    LLM-001, CORE-002

    ## Acceptance Criteria

    - [ ] Task classes are explicit
- [ ] Routing policy uses registered backend metadata
- [ ] Fallback expectations are defined

    ## Decision Blockers

    None

    ## Artifacts

    - None yet

    ## Notes
