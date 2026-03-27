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

closeout

## Status

done

## Trust

- resolution_state: done
- verification_state: reverified
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

- backlog-verification: .opencode/state/artifacts/history/exec-010/review/2026-03-27T07-32-25-991Z-backlog-verification.md (review) - Backlog verification for EXEC-010: PASS — nested redaction, max-depth, and truncation semantics verified correct
- reverification: .opencode/state/artifacts/history/exec-010/review/2026-03-27T07-32-46-344Z-reverification.md (review) - Trust restored using EXEC-010.

## Notes

- Evidence source: full-suite repair verification after deterministic Scafforge refresh on 2026-03-25.
- Validated on 2026-03-27: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py -q --tb=no` exits 0 after preserving container shape for sensitive dict/list keys and fixing the max-depth sentinel cutoff.

