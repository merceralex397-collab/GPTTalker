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

## Trust

- resolution_state: superseded
- verification_state: reverified
- finding_source: None
- source_ticket_id: EDGE-003
- source_mode: post_completion_issue

## Depends On

SETUP-004, CORE-005

## Follow-up Tickets

- EDGE-003

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
- backlog-verification: .opencode/state/reviews/edge-001-review-backlog-verification.md (review) - Backlog verification for EDGE-001: PASS

## Notes

