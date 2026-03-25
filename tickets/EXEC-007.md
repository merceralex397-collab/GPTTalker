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

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- source_ticket_id: EXEC-002
- source_mode: post_completion_issue

## Depends On

EXEC-004, EXEC-005

## Follow-up Tickets

None

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
- environment-bootstrap: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-25T23-02-26-471Z-environment-bootstrap.md (bootstrap) - Environment bootstrap failed.

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.

