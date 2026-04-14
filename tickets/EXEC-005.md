# EXEC-005: Align write_markdown and MCP transport response contracts with tests

## Summary

EXEC-005: Align write_markdown and MCP transport response contracts with tests — CLOSED. 6/6 scoped tests pass.

## Wave

9

## Lane

bugfix

## Parallel Safety

- parallel_safe: true
- overlap_risk: medium

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- finding_source: None
- source_ticket_id: EXEC-002
- source_mode: net_new_scope

## Depends On

None

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `write_markdown_handler()` accepts the contract-tested `node_id` argument shape without raising unexpected-keyword errors.
- [ ] `format_tool_response()` returns the MCP payload shape expected by the transport tests.
- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py -q --tb=no` passes the contract and MCP transport cases tied to these surfaces.
- [ ] The fix preserves current tool success, error, trace-id, and duration behavior for existing MCP responses.

## Artifacts

- planning: .opencode/state/artifacts/history/exec-005/planning/2026-03-25T18-05-23-233Z-planning.md (planning) - Plan for EXEC-005: Fix write_markdown_handler parameter names (node_id/repo_id/path) and format_tool_response nesting. Changes to markdown.py, __init__.py, and mcp.py.
- review: .opencode/state/artifacts/history/exec-005/review/2026-03-25T18-12-57-623Z-review.md (review) - Review for EXEC-005: APPROVED - Both issues correctly fixed, no blockers.
- implementation: .opencode/state/artifacts/history/exec-005/implementation/2026-03-25T18-27-39-839Z-implementation.md (implementation) - Implementation of EXEC-005: Fixed write_markdown_handler parameter names (node_id/repo_id/path) and format_tool_response nesting in mcp.py. All 3 files updated.
- qa: .opencode/state/artifacts/history/exec-005/qa/2026-03-25T18-27-52-344Z-qa.md (qa) - QA verification for EXEC-005: All acceptance criteria passed - scoped pytest (6 tests) all pass.
- smoke-test: .opencode/state/artifacts/history/exec-005/smoke-test/2026-03-25T18-28-00-022Z-smoke-test.md (smoke-test) [superseded] - EXEC-005 scoped fix VERIFIED - 6/6 scoped tests pass. Full suite failures are pre-existing.
- smoke-test: .opencode/state/artifacts/history/exec-005/smoke-test/2026-03-25T18-29-03-480Z-smoke-test.md (smoke-test) - EXEC-005 scoped fix VERIFIED - 6/6 scoped tests pass. Full suite failures are pre-existing.
- reverification: .opencode/state/artifacts/history/exec-005/review/2026-03-27T16-33-41-546Z-reverification.md (review) - Trust restored using EXEC-005.

## Notes


