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

closeout

## Status

done

## Depends On

CORE-005, OBS-001, POLISH-001

## Decision Blockers

None

## Acceptance Criteria

- [ ] Security regression suite covers path and target validation
- [ ] Log redaction behavior is tested
- [ ] Fail-closed expectations are enforced under error conditions

## Artifacts

- plan: .opencode/state/plans/polish-002-planning-plan.md (planning) - Planning for POLISH-002: Security regression tests and redaction hardening. Defines path traversal tests, target validation, redaction tests, and fail-closed behavior tests.
- implementation: .opencode/state/implementations/polish-002-implementation-implementation.md (implementation) - Implementation of POLISH-002: Created tests/hub/test_security.py with 23+ security regression tests covering path traversal, target validation, redaction, and fail-closed behavior.
- qa: .opencode/state/qa/polish-002-qa-qa.md (qa) - QA verification for POLISH-002: Security regression tests and redaction hardening. All 3 acceptance criteria verified.

## Notes


