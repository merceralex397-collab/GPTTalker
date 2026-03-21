# REPO-003: search_repo and git_status tools

## Summary

Implement text search and git status access through the node agent using bounded subprocess execution and structured result formatting.

## Wave

2

## Lane

repo-inspection

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

closeout

## Status

done

## Depends On

REPO-002

## Decision Blockers

None

## Acceptance Criteria

- [ ] Search uses bounded ripgrep execution
- [ ] Git status is exposed read-only
- [ ] Timeout and error handling are explicit

## Artifacts

- plan: .opencode/state/plans/repo-003-planning-plan.md (planning) - Implementation plan for REPO-003: search_repo and git_status tools. Defines bounded ripgrep search, read-only git status, hub handlers (search.py, git_operations.py), node-agent executor methods, HTTP endpoints, policy integration with READ_REPO_REQUIREMENT, explicit timeout handling (60s search, 30s git), new files to create, existing files to modify, and validation plan.
- implementation: .opencode/state/implementations/repo-003-implementation-implementation.md (implementation) - Implementation of REPO-003: search_repo and git_status tools. Created hub-side handlers (search.py, git_operations.py), node-agent executor methods (search_files, git_status), and updated operations endpoints with bounded ripgrep execution and read-only git status access.
- review: .opencode/state/reviews/repo-003-review-review.md (review) - Code review for REPO-003: search_repo and git_status tools. APPROVED - all acceptance criteria met: bounded ripgrep with path validation, read-only git operations, explicit timeout handling, READ_REPO_REQUIREMENT policy integration.
- qa: .opencode/state/qa/repo-003-qa-qa.md (qa) - QA verification for REPO-003: search_repo and git_status tools. All 3 acceptance criteria verified via code inspection - bounded ripgrep with path validation, read-only git commands, explicit timeout handling.
- backlog-verification: .opencode/state/reviews/repo-003-review-backlog-verification.md (review) - Backlog verification for REPO-003: PASS

## Notes


