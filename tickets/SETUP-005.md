# SETUP-005: Test, lint, and local validation scaffold

## Summary

Set up the repository validation baseline so future tickets can run pytest and ruff with predictable local conventions.

## Wave

0

## Lane

qa

## Parallel Safety

- parallel_safe: true
- overlap_risk: low

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- finding_source: None
- source_ticket_id: None
- source_mode: None

## Depends On

SETUP-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] Validation commands are documented and wired
- [ ] Test package layout is planned
- [ ] Ruff and pytest expectations match the brief

## Artifacts

- planning: .opencode/state/plans/setup-005-planning-planning.md (planning) - Implementation plan for SETUP-005: Test, lint, and local validation scaffold. Defines validation commands (Makefile, CLI entrypoints), test package layout (hub/node_agent/shared directories), pytest fixtures (async_db_session, test_client, mock registries), and documentation (docs/validation.md). All acceptance criteria addressed - no blockers.
- implementation: .opencode/state/implementations/setup-005-implementation-implementation.md (implementation) - Implementation of SETUP-005: Created validation scaffold with Makefile, validation scripts (validate.py, run_tests.py, run_lint.py), test package organization (hub/node_agent/shared directories), extended conftest.py with fixtures, and docs/validation.md documentation.
- review: .opencode/state/reviews/setup-005-review-review.md (review) - Code review for SETUP-005: Approved. Implementation matches the plan exactly - all validation commands wired, test package structure created with proper fixtures, Makefile targets functional, and documentation complete. All three acceptance criteria satisfied.
- qa: .opencode/state/qa/setup-005-qa-qa.md (qa) - QA verification for SETUP-005: Test, lint, and local validation scaffold. All 3 acceptance criteria passed - validation commands wired, test package layout correct, ruff and pytest configured properly.
- backlog-verification: .opencode/state/reviews/setup-005-review-backlog-verification.md (review) - Backlog verification for SETUP-005: PASS
- reverification: .opencode/state/artifacts/history/setup-005/review/2026-03-31T21-25-11-486Z-reverification.md (review) - Trust restored using SETUP-005.

## Notes


