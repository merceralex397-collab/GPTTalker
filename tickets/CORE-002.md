# CORE-002: Repo, write-target, and LLM service registries

## Summary

Define the structured registries for repos, markdown write targets, and LLM service aliases so later tools can validate every target explicitly.

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

- [ ] Repo registry model exists
- [ ] Write-target registry model exists
- [ ] LLM service alias model exists

## Artifacts

- planning: .opencode/state/plans/core-002-planning-planning.md (planning) - Implementation plan for CORE-002: Repo, write-target, and LLM service registries. Documents that tables/models/repositories already exist from SETUP-003, and defines the new work scope: DI providers for repositories in dependencies.py, and fail-closed policy classes (RepoPolicy, WriteTargetPolicy, LLMServicePolicy). Includes schema design, CRUD operations, implementation steps for 5 code files, validation plan, and integration points with later tickets.
- review: .opencode/state/reviews/core-002-review-review.md (review) - Code review for CORE-002: APPROVED. All 3 acceptance criteria met (models already exist from SETUP-003). Policy classes are technically sound with proper async/await, fail-closed behavior, and structured logging. DI providers correctly integrate with existing dependencies.py pattern. No blockers or missing decisions.
- implementation: .opencode/state/implementations/core-002-implementation-implementation.md (implementation) - Implementation of CORE-002: Created 3 policy classes (RepoPolicy, WriteTargetPolicy, LLMServicePolicy) for fail-closed validation, and added 6 DI providers in dependencies.py for repositories and policies.
- qa: .opencode/state/qa/core-002-qa-qa.md (qa) - QA verification for CORE-002: All 3 acceptance criteria verified - models exist in src/shared/models.py, DI providers added to dependencies.py, policy classes created and linting passes.
- backlog-verification: .opencode/state/reviews/core-002-review-backlog-verification.md (review) - Backlog verification for CORE-002: PASS
- reverification: .opencode/state/artifacts/history/core-002/review/2026-03-31T21-25-14-042Z-reverification.md (review) - Trust restored using CORE-002.

## Notes


