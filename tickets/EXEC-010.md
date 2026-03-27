# EXEC-010: Restore nested structured logging redaction semantics

## Summary

Despite the earlier scoped fix, full-suite validation still fails nested logging redaction cases. Restore dict/list shape preservation, list-item redaction, and max-depth behavior so shared structured logging matches the test contract.

## Wave

10

## Lane

shared-runtime

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

EXEC-006

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py -q --tb=no` exits 0.
- [ ] Nested dict and list structures preserve non-sensitive shape while leaf secrets redact.
- [ ] Max-depth handling returns the contract-tested sentinel value at the cutoff.
- [ ] Long-string truncation and sensitive-pattern coverage remain fail-closed.

## Artifacts

- None yet

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.
- Evidence refreshed on 2026-03-27: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v` still fails `test_redact_sensitive_nested`, `test_redact_sensitive_list`, and `test_redact_sensitive_max_depth` in `tests/shared/test_logging.py`.
