# EXEC-009: Repair node-agent executor timestamp and recent-commit behavior

## Summary

Node-agent executor validation still fails on directory timestamps and git status output. Replace the invalid UTC timestamp usage and make `recent_commits` reliable under the documented bootstrap environment so bounded node inspection can proceed.

## Wave

10

## Lane

node-agent

## Parallel Safety

- parallel_safe: true
- overlap_risk: medium

## Stage

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: EXEC-002
- source_mode: post_completion_issue

## Depends On

EXEC-003

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/node_agent/test_executor.py -q --tb=no` exits 0.
- [ ] `OperationExecutor.list_directory()` uses a Python 3.11-compatible UTC timestamp path.
- [ ] `OperationExecutor.git_status()` returns populated `recent_commits` data for temporary repos under the configured git identity.
- [ ] Executor allowed-path validation remains fail-closed.

## Artifacts

- None yet

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.

