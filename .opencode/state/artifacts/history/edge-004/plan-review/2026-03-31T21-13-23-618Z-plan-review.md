# Plan Review: EDGE-004 — Reconcile Cloudflare-specific ticket lineage after ngrok pivot

## Decision: APPROVED

## Rationale

The plan is **decision-complete** and ready for implementation. All three acceptance criteria are addressable through the planned `ticket_reconcile` actions, and the current evidence confirms most of the work is already done.

---

## Findings

### 1. Completeness — All Three Acceptance Criteria Are Addressable

| Criterion | Plan Coverage | Current Evidence |
|---|---|---|
| Historical Cloudflare-specific edge tickets are superseded or reconciled | Steps 2 & 3 use `ticket_reconcile` with `supersede_target: true` and `replacement_source_ticket_id: EDGE-003` for both EDGE-001 and EDGE-002 | **Already partially done**: EDGE-003 has `source_ticket_id: EDGE-001` and `source_mode: post_completion_issue`, establishing the supersession. FIX-013 has `follow_up_ticket_ids: [EDGE-004]`. EDGE-002 lacks explicit lineage to EDGE-003 in current manifest. |
| Pivot ticket lineage actions are no longer left as planned-only | Step 4 verifies restart surfaces; reconciliation artifact in Step 2 & 3 provides the "runtime evidence" required | **Restart surfaces confirm ngrok**: `START-HERE.md` line 23 and `context-snapshot.md` show ngrok as canonical and reference the ngrok-specific follow-ups from the March 31 pivot. `pivot_completed_ticket_lineage_actions` includes `supersede:EDGE-001`. |
| Restart surfaces and backlog views no longer suggest Cloudflare is current | Step 4 explicitly checks START-HERE, BOARD.md, and manifest | **ngrok.md exists** at `docs/ops/ngrok.md` (155 lines, comprehensive). **cloudflare-tunnel.md** now contains only a redirect notice ("Cloudflare Tunnel is no longer canonical... use ngrok Setup"). **node-registration.md** has zero Cloudflare references (confirmed via grep). BOARD.md still shows EDGE-001/EDGE-002 as "suspect" — this is the actionable gap the plan addresses. |

### 2. Feasibility — ticket_reconcile Is the Correct Tool

- **EDGE-001**: Already has implicit supersession from EDGE-003 (`source_ticket_id: EDGE-001`, `source_mode: post_completion_issue`). Plan adds explicit reconciliation via `ticket_reconcile` with `supersede_target: true`, creating a formal artifact and updating the manifest to reflect resolution_state: "superseded".

- **EDGE-002**: No explicit lineage to EDGE-003 exists in current manifest. Plan's Step 3 correctly identifies this gap. The "alternative: update docs directly" is unnecessary — grep confirms `node-registration.md` has zero Cloudflare references. The only required action for EDGE-002 is the `ticket_reconcile` to establish lineage.

- **No blockers**: Both source tickets (EDGE-003) are `done` and `trusted`. Bootstrap is `ready` (`workflow-state.json` line 371). EDGE-004 is `parallel_safe: true`, `overlap_risk: low`.

### 3. Spec Alignment — Correct Cloudflare Surfaces Identified

| Surface | Plan Inventory | Current Reality |
|---|---|---|
| HubConfig cloudflare_token | Correctly identified in Step 1 | Confirmed removed — EDGE-003 review (line 20) confirms "ngrok config fields: Already present in config.py" |
| docs/ops/cloudflare-tunnel.md | Correctly identified | Exists as redirect only — redirects to ngrok.md; this is an acceptable historical reference state |
| node-registration.md Cloudflare references | Plan's Step 3 flags this | **Already clean** — grep returned zero matches. No action needed on docs. |
| ngrok.md | Not listed as a gap | Exists (155 lines) and is comprehensive per EDGE-003 review |

### 4. Decision Blockers — None

No unresolved blockers. The plan correctly identifies the remaining gap as **ticket metadata reconciliation** (not runtime or docs work). The docs are already correct. The `ticket_reconcile` calls are the only required implementation step.

---

## Required Revisions

**None.** The plan is approved as-written.

---

## Validation Gaps

**None that block approval.** Two observations for implementation clarity:

1. **Step 3 "alternative" is unnecessary**: The plan mentions updating docs directly if Cloudflare references persist in `node-registration.md`. Grep confirms zero matches — the docs are already clean. The only required action for EDGE-002 is the `ticket_reconcile` to establish lineage.

2. **BOARD.md suspect status**: EDGE-001 and EDGE-002 appear as "suspect" on BOARD.md because they lack formal reconciliation. This is expected and is exactly what EDGE-004 fixes. No separate remediation is needed.

---

## Blockers / Missing Decisions

**None.**

---

## Summary

The plan correctly routes EDGE-004 through `ticket_reconcile` for both EDGE-001 and EDGE-002, pointing to EDGE-003 as the replacement source. The docs are already clean (cloudflare-tunnel.md is a redirect, node-registration.md has no Cloudflare references, ngrok.md is comprehensive). The restart surfaces already reflect ngrok as canonical. The only remaining work is formalizing the ticket lineage in the manifest, which the plan accomplishes. **Approve and proceed to implementation.**
