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

closeout

## Status

done

## Depends On

SETUP-004, CORE-005

## Decision Blockers

None

## Acceptance Criteria

- [ ] Tunnel configuration owner is explicit
- [ ] HTTPS public-edge boundary is documented in code and config
- [ ] Security constraints remain aligned with the brief

## Artifacts

- plan: .opencode/state/plans/edge-001-planning-plan.md (planning) - Planning for EDGE-001: Cloudflare Tunnel integration and public-edge config. Defines tunnel configuration, documentation, and integration approach.
- implementation: .opencode/state/implementations/edge-001-implementation-implementation.md (implementation) - Implementation of EDGE-001: Cloudflare Tunnel integration and public-edge config. Added tunnel config to HubConfig, created docs/ops/cloudflare-tunnel.md documentation.
- qa: .opencode/state/qa/edge-001-qa-qa.md (qa) - QA verification for EDGE-001: Cloudflare Tunnel integration and public-edge config. All 3 acceptance criteria verified.

## Notes


