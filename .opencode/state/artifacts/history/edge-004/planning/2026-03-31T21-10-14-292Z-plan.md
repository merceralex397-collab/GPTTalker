# Planning Artifact: EDGE-004

## Ticket
- **ID**: EDGE-004
- **Title**: Reconcile Cloudflare-specific ticket lineage after ngrok pivot
- **Lane**: edge
- **Wave**: 12
- **Stage**: planning

## Summary
Use the canonical ticket tools to supersede or reconcile the historical Cloudflare-specific edge tickets so the backlog matches the ngrok architecture accepted in the March 31 pivot.

## Background

The March 31 architecture-change pivot replaced Cloudflare Tunnel with ngrok as the public HTTPS edge provider. EDGE-003 (Wave 12) completed the ngrok runtime migration. However, two historical tickets still carry Cloudflare-specific assumptions:

1. **EDGE-001** (Wave 5): "Cloudflare Tunnel integration and public-edge config" — marked done but contains Cloudflare-specific config fields and documentation
2. **EDGE-002** (Wave 5): "Node registration bootstrap and operator config docs" — operator docs reference Cloudflare Tunnel setup

The pivot canonical brief states:
> Unresolved follow-up:
> - Replace Cloudflare-specific runtime/config/docs/tests with ngrok-backed equivalents and verify startup and health behavior.
> - Reconcile or supersede historical Cloudflare-specific tickets so the backlog matches the post-pivot architecture.

## Scope

This ticket covers **ticket lineage reconciliation only** — updating the manifest and ticket relationships to reflect that Cloudflare is no longer canonical. Runtime ngrok configuration was already completed in EDGE-003 and prior fixes.

## Implementation Steps

### Step 1: Inventory Cloudflare-specific tickets

From `tickets/manifest.json`:

| Ticket | Title | Cloudflare-specific Surface |
|--------|-------|---------------------------|
| EDGE-001 | Cloudflare Tunnel integration and public-edge config | HubConfig fields (cloudflare_token), docs/ops/cloudflare-tunnel.md |
| EDGE-002 | Node registration bootstrap and operator config docs | docs/ops/node-registration.md references Cloudflare Tunnel |

### Step 2: Reconcile EDGE-001 lineage

EDGE-001 is marked `done` with `follow_up_ticket_ids: ["EDGE-003"]`. However, the Cloudflare-specific runtime code in EDGE-001 was already superseded by the ngrok migration in EDGE-003.

**Action**: Use `ticket_reconcile` to:
- Set `replacement_source_ticket_id: "EDGE-003"` (the ngrok runtime migration that superseded the Cloudflare-specific parts)
- Set `supersede_target: true` to mark EDGE-001 as superseded by the pivot
- Add a reconciliation artifact noting that runtime concerns were addressed in EDGE-003

### Step 3: Reconcile EDGE-002 docs lineage

EDGE-002 contains operator documentation for node registration that references Cloudflare Tunnel. The docs need updating to reflect ngrok as the canonical public-edge setup.

**Action**: Use `ticket_reconcile` to:
- Set `replacement_source_ticket_id: "EDGE-003"` (the ngrok migration that updated the edge docs)
- Note that EDGE-002 docs have been updated by the ngrok pivot work
- Alternatively: update the docs directly if the Cloudflare references are still present after EDGE-003

### Step 4: Verify restart surfaces

After reconciliation:
- `START-HERE.md` must show ngrok as current edge architecture
- `tickets/BOARD.md` must not list Cloudflare as active edge solution
- `tickets/manifest.json` must not have any active Cloudflare-specific tickets

## Acceptance Criteria Verification

| Criterion | Verification |
|-----------|--------------|
| Historical Cloudflare-specific edge tickets are superseded or reconciled | EDGE-001 and EDGE-002 show replacement lineage to EDGE-003 in manifest |
| Pivot ticket lineage actions are no longer left as planned-only | ticket_reconcile artifacts exist with runtime evidence |
| Restart surfaces no longer suggest Cloudflare is current | Derived surfaces (START-HERE, BOARD) reviewed and updated |

## Canonical Artifact Paths

| Artifact | Path |
|----------|------|
| This plan | `.opencode/state/plans/edge-004-planning-plan.md` |
| Reconciliation artifact | `.opencode/state/reviews/edge-004-review-ticket-reconciliation.md` |

## Dependencies

- EDGE-003 (completed) — provides the ngrok runtime replacement that supersedes Cloudflare

## Risks

- **Low risk**: Ticket lineage work is metadata-only; no runtime code changes
- **Parallel safe**: Yes — EDGE-004 is `parallel_safe: true`, `overlap_risk: low`
