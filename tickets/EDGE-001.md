    # EDGE-001: Cloudflare Tunnel integration and public-edge config

    ## Summary

    Define and implement the public-edge path through Cloudflare Tunnel so ChatGPT can reach the hub over HTTPS without exposing inbound ports.

    ## Wave

    5

    ## Lane

    edge

    ## Parallel Safety

    - parallel_safe: true
    - overlap_risk: low

    ## Stage

    planning

    ## Status

    todo

    ## Depends On

    SETUP-004, CORE-005

    ## Acceptance Criteria

    - [ ] Tunnel configuration owner is explicit
- [ ] HTTPS public-edge boundary is documented in code and config
- [ ] Security constraints remain aligned with the brief

    ## Decision Blockers

    None

    ## Artifacts

    - None yet

    ## Notes
