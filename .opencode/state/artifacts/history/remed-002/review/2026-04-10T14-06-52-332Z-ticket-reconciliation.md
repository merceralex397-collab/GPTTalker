# Ticket Reconciliation

## Canonical Source

- source_ticket_id: REMED-002
- target_ticket_id: REMED-005
- replacement_source_ticket_id: REMED-002
- replacement_source_mode: post_completion_issue

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/remed-002/smoke-test/2026-04-10T03-41-09-745Z-smoke-test.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: true

## Reason

REMED-005 source_ticket_id points to superseded FIX-023. The finding EXEC-REMED-001 was confirmed stale by REMED-002 (last authoritative remediation ticket in the chain). REMED-005 is a sequential split child of the superseded FIX-023 and has no remaining independent work.
