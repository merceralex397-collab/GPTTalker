# START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

GPTTalker

## Current State

The repo is operating under the managed OpenCode workflow. Use the canonical state files below instead of memory or raw ticket prose.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/manifest.json
6. tickets/BOARD.md

## Current Or Next Ticket

- ID: EXEC-008
- Title: Close remaining hub path and write-target security edge cases
- Wave: 10
- Lane: security
- Stage: smoke-test
- Status: smoke_test
- Resolution: open
- Verification: suspect

## Dependency Status

- current_ticket_done: no
- dependent_tickets_waiting_on_current: EXEC-012

## Generation Status

- handoff_status: workflow verification pending
- process_version: 6
- parallel_mode: sequential
- pending_process_verification: true
- repair_follow_on_required: false
- repair_follow_on_next_stage: none
- repair_follow_on_verification_passed: true
- repair_follow_on_handoff_allowed: true
- repair_follow_on_updated_at: 2026-03-27T04:22:29Z
- bootstrap_status: ready
- bootstrap_proof: .opencode/state/artifacts/history/exec-007/bootstrap/2026-03-26T03-37-12-985Z-environment-bootstrap.md

## Post-Generation Audit Status

- audit_or_repair_follow_up: follow-up required
- reopened_tickets: none
- done_but_not_fully_trusted: SETUP-001, SETUP-002, SETUP-003, SETUP-004, SETUP-005, CORE-001, CORE-002, CORE-003, CORE-004, CORE-005, CORE-006, REPO-001, REPO-002, REPO-003, WRITE-001, LLM-001, LLM-002, LLM-003, CTX-001, CTX-002, CTX-003, CTX-004, XREPO-001, XREPO-002, XREPO-003, SCHED-001, SCHED-002, OBS-001, OBS-002, EDGE-001, EDGE-002, POLISH-001, POLISH-002, POLISH-003, FIX-001, FIX-002, FIX-003, FIX-004, FIX-005, FIX-006, FIX-007, FIX-008, FIX-009, FIX-010, FIX-011, FIX-012, FIX-013, FIX-014, FIX-015, FIX-016, FIX-017
- pending_reverification: none
- repair_follow_on_blockers: none

## Known Risks

- Historical completion should not be treated as fully trusted until pending process verification is cleared.
- Some done tickets are not fully trusted yet; use the backlog verifier before relying on earlier closeout.
- Downstream tickets EXEC-012 remain formally blocked until EXEC-008 reaches done.

## Next Action

Keep EXEC-008 as the foreground ticket and continue its lifecycle from smoke-test. Historical done-ticket reverification stays secondary until the active open ticket is resolved.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
