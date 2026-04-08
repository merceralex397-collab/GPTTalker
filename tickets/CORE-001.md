# CORE-001: Node registry and node health model

## Summary

Implement the hub-side node registry schema, CRUD path, and health metadata used to track managed machines.

## Wave

1

## Lane

registry

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- source_ticket_id: None
- source_mode: None

## Depends On

SETUP-003, SETUP-004

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Node registry schema is defined
- [ ] Health metadata model is explicit
- [ ] Unknown nodes fail closed

## Artifacts

- planning: .opencode/state/plans/core-001-planning-planning.md (planning) - Implementation plan for CORE-001: Node registry and node health model. Defines health metadata model (NodeHealth), health polling service (NodeHealthService), fail-closed policy engine (NodePolicy), database migration for health columns, and integration points with existing SQLite and FastAPI layers.
- implementation: .opencode/state/implementations/core-001-implementation-implementation.md (implementation) - Implementation of CORE-001: Node registry and node health model. Created NodeHealth and NodeHealthService classes for health polling, NodePolicy for fail-closed access control, updated node repository with health methods, added migration v2 for health columns, and integrated DI providers.
- review: .opencode/state/reviews/core-001-review-review.md (review) - Code review for CORE-001: Node registry and node health model. APPROVED with observations. All 3 acceptance criteria met. Medium severity issue: incorrect latency measurement in health check. Low severity: missing trace_id, unused NodeHealthDetail schema. Implementation is production-ready with proper fail-closed behavior.
- qa: .opencode/state/qa/core-001-qa-qa.md (qa) - QA verification for CORE-001: Node registry and node health model. All 3 acceptance criteria verified - node registry schema defined via migration v2, health metadata model explicit with NodeHealth/NodeHealthStatus/NodeHealthDetail, fail-closed behavior confirmed in NodePolicy.validate_node_access().
- backlog-verification: .opencode/state/reviews/core-001-review-backlog-verification.md (review) - Backlog verification for CORE-001: PASS
- reverification: .opencode/state/artifacts/history/core-001/review/2026-03-31T21-25-12-512Z-reverification.md (review) - Trust restored using CORE-001.

## Notes


