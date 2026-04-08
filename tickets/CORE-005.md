# CORE-005: Policy engine and normalized path validation

## Summary

Build the fail-closed policy engine for nodes, repos, write targets, service aliases, and normalized file paths.

## Wave

1

## Lane

security

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

SETUP-002, SETUP-004

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Unknown targets are rejected explicitly
- [ ] Path normalization rules are central and reusable
- [ ] Write and read scopes are separated cleanly

## Artifacts

- planning: .opencode/state/plans/core-005-planning-planning.md (planning) - Implementation plan for CORE-005: Policy engine and normalized path validation. Updated to include ValidationResult and PathValidationResult dataclass definitions with their required fields. Defines PathNormalizer utility, OperationScope/ValidationContext, PolicyEngine orchestration, and DI integration.
- implementation: .opencode/state/implementations/core-005-implementation-implementation.md (implementation) - Implementation of CORE-005: Created PolicyEngine with path normalization utility (PathNormalizer), operation scope definitions (OperationScope, ValidationContext), and unified policy orchestration. Updated __init__.py exports and added DI provider in dependencies.py. All acceptance criteria met.
- review: .opencode/state/reviews/core-005-review-review.md (review) - Code review for CORE-005: Policy engine and normalized path validation. APPROVED - all 3 acceptance criteria met (unknown target rejection, central path normalization, scope separation). Low-severity observations noted for scope naming and path check redundancy.
- qa: .opencode/state/qa/core-005-qa-qa.md (qa) - QA verification for CORE-005: All 3 acceptance criteria verified via code inspection - unknown targets rejected explicitly, path normalization centralized and reusable, read/write scopes cleanly separated.
- backlog-verification: .opencode/state/reviews/core-005-review-backlog-verification.md (review) - Backlog verification for CORE-005: PASS
- reverification: .opencode/state/artifacts/history/core-005/review/2026-03-31T21-25-17-628Z-reverification.md (review) - Trust restored using CORE-005.

## Notes


