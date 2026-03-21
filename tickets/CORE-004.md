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

closeout

## Status

done

## Depends On

CORE-001, CORE-003

## Decision Blockers

None

## Acceptance Criteria

- [ ] Hub-to-node auth model is enforced
- [ ] HTTP client timeouts are explicit
- [ ] Health polling integrates with the node registry

## Artifacts

- planning: .opencode/state/plans/core-004-planning-planning.md (planning) - Implementation plan for CORE-004: Hub-to-node client, auth, and health polling. Defines the HubNodeClient class, NodeAuthHandler for API key authentication, timeout configuration via HubConfig, HTTP client lifecycle in lifespan, and DI providers. Integrates with existing NodeHealthService. Addresses all 3 acceptance criteria: hub-to-node auth model enforced, explicit HTTP client timeouts, and health polling integration with node registry.
- implementation: .opencode/state/implementations/core-004-implementation-implementation.md (implementation) - Implementation of CORE-004: Created hub-to-node HTTP client (HubNodeClient), authentication handler (NodeAuthHandler), updated config with timeout/pool settings, lifespan to initialize HTTP client, dependencies for DI, and integrated auth with node health service.
- review: .opencode/state/reviews/core-004-review-review.md (review) - Fix verification for CORE-004: All 3 claimed fixes confirmed - config attribute corrected, JSON error handling added, datetime deprecation resolved.
- qa: .opencode/state/qa/core-004-qa-qa.md (qa) - QA verification for CORE-004: All 3 acceptance criteria verified via code inspection. Hub-to-node auth model enforced (Bearer token), explicit HTTP client timeouts, and health polling integration with node registry confirmed.
- backlog-verification: .opencode/state/reviews/core-004-review-backlog-verification.md (review) - Backlog verification for CORE-004: PASS

## Notes


