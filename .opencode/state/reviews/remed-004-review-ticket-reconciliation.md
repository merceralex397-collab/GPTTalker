# Ticket Reconciliation

## Canonical Source

- source_ticket_id: REMED-004
- target_ticket_id: FIX-020
- replacement_source_ticket_id: FIX-020
- replacement_source_mode: post_completion_issue

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/fix-020/smoke-test/2026-04-10T13-33-46-794Z-smoke-test.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: false

## Reason

REMED-004 finding source is EXEC001 (Python import failure). The authoritative evidence is the FIX-020 smoke test that passed (exit 0) confirming `from src.node_agent.main import app` works. EXEC001 was already verified fixed in EXEC-001 and confirmed in FIX-020. REMED-004 is a sequential split child of FIX-023, which is now reconciled as stale duplicate of FIX-020. Reconciling REMED-004 as stale follow-up whose authoritative source is FIX-020 (which carries the import verification).
