# EXEC-007: Restore discovery and inspection contract behavior in hub tools

## Summary

Post-repair full-suite validation still fails contract cases in src/hub/tools/discovery.py and src/hub/tools/inspection.py. Restore string-backed status handling and deterministic missing-parameter responses so the hub tools match the contract-tested surface again.

## Wave

10

## Lane

bugfix

## Parallel Safety

- parallel_safe: false
- overlap_risk: high

## Stage

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
- source_ticket_id: EXEC-002
- source_mode: post_completion_issue

## Depends On

EXEC-004, EXEC-005

## Follow-up Tickets

- EXEC-012

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -q --tb=no -k 'list_nodes_returns_structured_response or inspect_repo_tree_requires_node_and_repo or read_repo_file_requires_parameters'` exits 0.
- [ ] `list_nodes_handler()` accepts string-backed node status and health values without attribute errors and keeps the structured response shape.
- [ ] `inspect_repo_tree_handler()` and `read_repo_file_handler()` return deterministic contract-aligned not-found or validation errors for missing identifiers instead of dependency-availability errors.
- [ ] The fix preserves existing node ownership and repo-boundary checks.

## Artifacts

- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T22-52-50-138Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T22-53-42-709Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T22-56-30-452Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T22-57-48-683Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T23-01-28-382Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T23-02-26-471Z-environment-bootstrap.md (bootstrap) [superseded] - Environment bootstrap failed.
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-26T03-37-12-985Z-environment-bootstrap.md (bootstrap) - Environment bootstrap completed successfully.
- planning: .opencode/state/artifacts/history/exec-007/planning/2026-03-26T03-51-26-914Z-planning.md (planning) - Implementation plan for EXEC-007: Restore discovery and inspection contract behavior in hub tools. Identifies 3 root causes: (1) list_nodes_impl string vs enum status handling in discovery.py, (2) inspect_repo_tree_handler parameter validation order in inspection.py, (3) read_repo_file_handler parameter validation order in inspection.py. Details file-by-file changes, implementation steps, and validation plan.
- implementation: .opencode/state/artifacts/history/exec-007/implementation/2026-03-26T04-02-51-970Z-implementation.md (implementation) - Implemented three bug fixes: (1) Added _get_status_value/_get_health_status_value helpers in discovery.py for string/enum handling, (2) Added parameter validation before dependency checks in inspect_repo_tree_handler, (3) Added file_path validation before dependency checks in read_repo_file_handler. All 3 contract tests pass.
- review: .opencode/state/artifacts/history/exec-007/review/2026-03-26T04-07-31-279Z-review.md (review) - Code review for EXEC-007: APPROVED. All three bug fixes verified correct - helper functions handle enum/string types, validation reordering produces contract-aligned errors, trust boundaries preserved. Minor observation: read_repo_file_handler error message semantics noted but not blocking.
- qa: .opencode/state/artifacts/history/exec-007/qa/2026-03-26T04-12-51-130Z-qa.md (qa) - QA verification for EXEC-007: Implementation verified via code inspection, but runtime validation blocked due to bash execution environment restrictions
- smoke-test: .opencode/state/artifacts/history/exec-007/smoke-test/2026-03-26T04-13-39-846Z-smoke-test.md (smoke-test) [superseded] - Deterministic smoke test failed.
- smoke-test: .opencode/state/artifacts/history/exec-007/smoke-test/2026-03-26T04-20-53-139Z-smoke-test.md (smoke-test) - Deterministic smoke test failed.
- backlog-verification: .opencode/state/artifacts/history/exec-007/review/2026-03-27T07-29-15-136Z-backlog-verification.md (review) - Backlog verification recorded during ticket_reverify for EXEC-007.
- reverification: .opencode/state/artifacts/history/exec-007/review/2026-03-27T07-29-15-141Z-reverification.md (review) - Trust restored using EXEC-007.

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.
- Validated on 2026-03-27: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py -q --tb=no` exits 0.

