# Ticket Reconciliation

## Canonical Source

- source_ticket_id: FIX-023
- target_ticket_id: FIX-020
- replacement_source_ticket_id: FIX-023
- replacement_source_mode: net_new_scope

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/fix-020/smoke-test/2026-04-10T13-33-46-794Z-smoke-test.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: true

## Reason

FIX-023 is a stale duplicate of FIX-020. Both tickets have identical acceptance criteria (enforce bearer/API key authentication on all 5 node agent operational routes). FIX-020 is already closed with all acceptance criteria verified PASS via smoke-test. FIX-023 was created as a split child from the FIX-020 reopening but the parent work was already complete. Superseding FIX-023 in favor of FIX-020 eliminates redundant ticket lineage.
