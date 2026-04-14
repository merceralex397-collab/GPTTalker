# Planning Artifact — REMED-013

## Ticket

- **ID**: REMED-013
- **Title**: Remediation review artifact does not contain runnable command evidence
- **Wave**: 32
- **Lane**: remediation
- **Finding source**: EXEC-REMED-001
- **Source ticket**: REMED-007
- **Split kind**: parallel_independent

## Affected Surfaces

- `tickets/manifest.json` — REMED-013 ticket entry (artifacts array will be populated)
- `.opencode/state/reviews/remed-002-review-ticket-reconciliation.md` — reconciliation artifact linking REMED-005 to REMED-002

## Investigation Summary

The finding EXEC-REMED-001 ("Remediation review artifact does not contain runnable command evidence") was originally logged against the remediation chain rooted at FIX-020. Subsequent remediation tickets (REMED-008, REMED-011, REMED-012) each independently confirmed the finding is **stale** — all required fixes (FastAPI DI anti-pattern correction, `from __future__ import annotations` forward-reference hygiene, `MCPProtocolHandler.initialize()` lifespan integration) are confirmed present in the current codebase.

The affected surface for this ticket — `remed-002-review-ticket-reconciliation.md` — records the reconciliation of REMED-005 (superseded) against REMED-002. That reconciliation artifact itself demonstrates the correct command-record format and PASS results, confirming the finding is stale.

## Plan

No code changes are required. The finding is stale.

1. Write this planning artifact confirming stale-finding conclusion.
2. Advance to `plan_review` and receive approval.
3. Advance to `implementation` — document "no code changes needed" summary.
4. Advance to `review` — produce review artifact with QA section containing 3 import verification commands using the `UV_CACHE_DIR=/tmp/uv-cache uv run python -c '...'` command pattern, raw output embedded inline, and explicit PASS/FAIL results.
5. Advance to `qa` — verify QA section format matches the winning pattern from REMED-012.
6. Run smoke test (same 3 commands as QA verification).
7. Advance to `closeout`.

## Acceptance Criteria

1. The validated finding `EXEC-REMED-001` no longer reproduces.
2. Current quality checks rerun with evidence tied to the fix approach: For remediation tickets with `finding_source`, require the review artifact to record the exact command run, include raw command output, and state the explicit PASS/FAIL result before the review counts as trustworthy closure.

## Verification Commands

The following 3 import checks will be used as the QA command record:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.main import app; print("OK")'
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.node_agent.main import app; print("OK")'
UV_CACHE_DIR=/tmp/uv-cache uv run python -c 'from src.hub.mcp import MCPProtocolHandler; print("OK")'
```

All three must exit 0 with output `OK`.

## Dependency Status

- `depends_on`: none (parallel_independent split from REMED-007)
- No tickets block REMED-013
- REMED-013 does not block any other ticket
