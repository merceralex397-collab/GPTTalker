    # POLISH-002: Security regression tests and redaction hardening

    ## Summary

    Harden the security and observability surfaces with targeted regression tests for path traversal, secret redaction, and fail-closed behavior.

    ## Wave

    6

    ## Lane

    qa

    ## Parallel Safety

    - parallel_safe: false
    - overlap_risk: medium

    ## Stage

    planning

    ## Status

    todo

    ## Depends On

    CORE-005, OBS-001, POLISH-001

    ## Acceptance Criteria

    - [ ] Security regression suite covers path and target validation
- [ ] Log redaction behavior is tested
- [ ] Fail-closed expectations are enforced under error conditions

    ## Decision Blockers

    None

    ## Artifacts

    - None yet

    ## Notes
