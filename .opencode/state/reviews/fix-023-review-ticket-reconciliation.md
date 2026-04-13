# Ticket Reconciliation

## Canonical Source

- source_ticket_id: FIX-023
- target_ticket_id: FIX-020
- replacement_source_ticket_id: FIX-020
- replacement_source_mode: post_completion_issue

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/fix-020/smoke-test/2026-04-10T13-33-46-794Z-smoke-test.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: false

## Reason

FIX-023 is a stale duplicate of FIX-020. Both have identical acceptance criteria for enforcing auth on node agent routes. FIX-020 is already done/reverified with full smoke-test artifact. FIX-023 was created as a split parent but its scope was already completed. Reconciling FIX-023 as stale duplicate whose authoritative source is FIX-020.
