# Ticket Reconciliation

## Canonical Source

- source_ticket_id: FIX-020
- target_ticket_id: FIX-023
- replacement_source_ticket_id: FIX-020
- replacement_source_mode: post_completion_issue

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/fix-020/smoke-test/2026-04-10T13-33-46-794Z-smoke-test.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: true

## Reason

FIX-023 is a stale duplicate of FIX-020. Both tickets have identical acceptance criteria for enforcing auth on node-agent operational routes. FIX-020 is done/reverified with PASSING smoke-test artifact confirming import succeeds and auth is enforced. FIX-023 was created as a split parent but its scope was already completed in FIX-020. The prior reversed reconciliation calls created a self-reconciled impossible lineage (FIX-023 artifacts reconciled FIX-020 against FIX-020). This reconcile corrects that by treating FIX-020 as the authoritative source and superseding FIX-023 as the stale duplicate.
