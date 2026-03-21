# Context Snapshot

## Project

GPTTalker

## Active Ticket

- ID: FIX-015
- Title: Fix Task UUID handling and CLI entrypoint packaging
- Stage: closeout
- Status: done
- Approved plan for this ticket: yes

## Process State

- process_version: 4
- pending_process_verification: false
- parallel_mode: parallel-lanes
- process_changed_at: 2026-03-20T15:39:45Z
- process_note: Deterministic managed-surface replacement approved by user after clean audit to refresh scaffold-managed repo structure.

## Ticket Summary

Two issues: (1) TaskRepository.create accepts UUID|str but _row_to_task always parses as UUID, crashing on string IDs. (2) Console scripts point to scripts.* but package discovery only includes src*.

## Recent Artifacts

- plan: .opencode/state/plans/fix-015-planning-plan.md (planning)
- review: .opencode/state/reviews/fix-015-review-review.md (review)
- implementation: .opencode/state/implementations/fix-015-implementation-implementation.md (implementation)
- qa: .opencode/state/qa/fix-015-qa-qa.md (qa)
- smoke-test: .opencode/state/smoke-tests/fix-015-smoke-test-smoke-test.md (smoke-test)
## Note

Regenerated to reflect current active ticket after state review

## Next Useful Step

Use the team leader or the next required specialist for the current stage.
