# GPTTalker — START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

GPTTalker

## Current State

The repo is operating under the managed OpenCode workflow. The workflow layer was repaired on March 25, 2026 to restore closed-ticket reverification, contradiction-stop handling, and transcript-aware lifecycle guidance. Bootstrap is ready, the dev environment is installed, and Wave 10 remediation tickets now track the remaining real source failures plus lint debt.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/BOARD.md
6. tickets/manifest.json

## Current Or Next Ticket

- ID: EXEC-007
- Title: Restore discovery and inspection contract behavior in hub tools
- Wave: 10
- Lane: bugfix
- Stage: planning
- Status: todo
- Resolution: open
- Verification: suspect

## Generation Status

- handoff_status: ready for continued development
- process_version: 5
- parallel_mode: sequential
- pending_process_verification: true
- bootstrap_status: ready
- bootstrap_proof: .opencode/state/artifacts/history/exec-001/bootstrap/2026-03-25T12-05-00-000Z-environment-bootstrap.md
- process_changed_at: 2026-03-25T22:19:11Z
- process_note: Diagnosis-backed Scafforge workflow repair for closed-ticket reverification, contradiction-stop guidance, and transcript-aware lifecycle hardening after diagnosis/20260325-221327.
- process_state: Historical done tickets remain subject to backlog reverification while Wave 10 source remediation is open.

## Post-Generation Audit Status

- audit_or_repair_follow_up: workflow repair applied; remaining work is backlog reverification plus EXEC-007 through EXEC-011
- reopened_tickets: none
- done_but_not_fully_trusted: SETUP-001, SETUP-002, SETUP-003, SETUP-004, SETUP-005, CORE-001, CORE-002, CORE-003, CORE-004, CORE-005, CORE-006, REPO-001, REPO-002, REPO-003, WRITE-001, LLM-001, LLM-002, LLM-003, CTX-001, CTX-002, CTX-003, CTX-004, XREPO-001, XREPO-002, XREPO-003, SCHED-001, SCHED-002, OBS-001, OBS-002, EDGE-001, EDGE-002, POLISH-001, POLISH-002, POLISH-003, FIX-001, FIX-002, FIX-003, FIX-004, FIX-005, FIX-006, FIX-007, FIX-008, FIX-009, FIX-010, FIX-011, FIX-012, FIX-013, FIX-014, FIX-015, FIX-016, FIX-017
- pending_reverification: none

## Known Risks

- Historical completion should not be treated as fully trusted until pending process verification is cleared.
- The workflow is no longer deadlocked, but backlog reverification still has to clear affected done tickets under the repaired contract.
- The full test suite still has 13 real failures routed into EXEC-007 through EXEC-010.
- `ruff check .` reports 51 source and test lint violations routed into EXEC-011.

## Next Action

Plan EXEC-007, then continue EXEC-008 through EXEC-011 as the remaining remediation wave. Keep `pending_process_verification` true until the backlog verifier clears the affected historical done tickets through the repaired `ticket_reverify` path.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
