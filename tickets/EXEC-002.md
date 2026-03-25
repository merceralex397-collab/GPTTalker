# EXEC-002: Restore pytest collection and full test execution after node-agent import fix

## Summary

Audit reproduced a test collection failure on March 24, 2026 in the repo virtualenv. `.venv/bin/pytest tests/ --collect-only -q --tb=no` aborts at `tests/node_agent/test_executor.py` because importing the node-agent stack triggers the same FastAPI dependency error. After the import fix lands, re-establish clean collection and a passing test suite with command-backed evidence.

## Wave

9

## Lane

bugfix

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

planning

## Status

ready

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: None
- source_mode: net_new_scope

## Depends On

EXEC-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `.venv/bin/pytest tests/ --collect-only -q --tb=no` exits 0 with no collection errors.
- [ ] `.venv/bin/pytest tests/ -q --tb=no` exits 0.
- [ ] The QA evidence records pass/fail counts and raw command output rather than a prose-only summary.
- [ ] Any remaining test failures are either fixed in scope or split into separately tracked follow-up tickets with concrete evidence.

## Artifacts

- None yet

## Notes


