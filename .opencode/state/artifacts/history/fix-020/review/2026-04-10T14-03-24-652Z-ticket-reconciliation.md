# Ticket Reconciliation

## Canonical Source

- source_ticket_id: FIX-020
- target_ticket_id: REMED-004
- replacement_source_ticket_id: FIX-020
- replacement_source_mode: post_completion_issue

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/fix-020/smoke-test/2026-04-10T13-33-46-794Z-smoke-test.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: true

## Reason

REMED-004 is a sequential split child of FIX-023 tracking EXEC001 (Python import failure). FIX-023 is now superseded as a stale duplicate of FIX-020. The authoritative evidence for EXEC001 is the FIX-020 smoke test that passed (exit 0) confirming `from src.node_agent.main import app` works. EXEC001 was already verified fixed in EXEC-001 and confirmed in FIX-020 smoke test. REMED-004 should be superseded in favor of its finding-source anchor FIX-020.
