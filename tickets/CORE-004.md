    # CORE-004: Hub-to-node client, auth, and health polling

    ## Summary

    Implement the authenticated hub-to-node HTTP client, timeout policy, and polling path used to reach node agents over Tailscale.

    ## Wave

    1

    ## Lane

    node-connectivity

    ## Parallel Safety

    - parallel_safe: false
    - overlap_risk: high

    ## Stage

    planning

    ## Status

    todo

    ## Depends On

    CORE-001, CORE-003

    ## Acceptance Criteria

    - [ ] Hub-to-node auth model is enforced
- [ ] HTTP client timeouts are explicit
- [ ] Health polling integrates with the node registry

    ## Decision Blockers

    None

    ## Artifacts

    - None yet

    ## Notes
