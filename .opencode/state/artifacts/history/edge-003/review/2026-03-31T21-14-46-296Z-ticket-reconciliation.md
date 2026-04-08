# Ticket Reconciliation

## Canonical Source

- source_ticket_id: EDGE-003
- target_ticket_id: EDGE-002
- replacement_source_ticket_id: EDGE-003
- replacement_source_mode: post_completion_issue

## Evidence

- evidence_artifact_path: .opencode/state/artifacts/history/edge-003/qa/2026-03-31T14-36-50-688Z-qa.md

## Applied Reconciliation

- removed_dependency_on_source: false
- superseded_target: true

## Reason

EDGE-002 contains operator documentation for node registration that referenced Cloudflare Tunnel. The ngrok pivot (EDGE-003) updated the edge documentation to use ngrok as the canonical public-edge setup. This reconciliation formally marks EDGE-002 as superseded by EDGE-003 in manifest lineage, with the ngrok migration providing the updated docs.
