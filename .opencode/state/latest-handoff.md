# START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

GPTTalker

## Current State

The repo is operating under the managed OpenCode workflow. Use the canonical state files below instead of memory or raw ticket prose.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/AGENT-DELEGATION.md
4. docs/spec/CANONICAL-BRIEF.md
5. docs/process/workflow.md
6. tickets/manifest.json
7. tickets/BOARD.md

## Current Or Next Ticket

- ID: EXEC-011
- Title: Reduce repo-wide ruff violations to zero
- Wave: 10
- Lane: hardening
- Stage: closeout
- Status: done
- Resolution: done
- Verification: trusted

## Dependency Status

- current_ticket_done: yes
- dependent_tickets_waiting_on_current: none
- split_child_tickets: none

## Generation Status

- handoff_status: repair follow-up required
- process_version: 7
- parallel_mode: sequential
- pending_process_verification: true
- repair_follow_on_outcome: managed_blocked
- repair_follow_on_required: true
- repair_follow_on_next_stage: project-skill-bootstrap
- repair_follow_on_verification_passed: false
- repair_follow_on_updated_at: 2026-04-07T22:18:21Z
- pivot_in_progress: false
- pivot_class: none
- pivot_changed_surfaces: none
- pivot_pending_stages: none
- pivot_completed_stages: none
- pivot_pending_ticket_lineage_actions: none
- pivot_completed_ticket_lineage_actions: none
- post_pivot_verification_passed: false
- bootstrap_status: ready
- bootstrap_proof: .opencode/state/artifacts/history/exec-011/bootstrap/2026-03-28T16-33-16-169Z-environment-bootstrap.md
- bootstrap_blockers: none

## Post-Generation Audit Status

- audit_or_repair_follow_up: follow-up required
- reopened_tickets: none
- done_but_not_fully_trusted: none
- pending_reverification: none
- repair_follow_on_blockers: project-skill-bootstrap must still run: Repo-local skills still contain generic placeholder/model drift that must be regenerated with project-specific content. | ticket-pack-builder must still run: Repair left remediation or reverification follow-up that must be routed into the repo ticket system. | Post-repair verification failed repair-contract consistency checks: placeholder_local_skills_survived_refresh.
- pivot_pending_stages: none
- pivot_pending_ticket_lineage_actions: none

## Code Quality Status

- last_build_result: pass @ 2026-03-28T16:39:25.444Z
- last_test_run_result: pass @ 2026-03-28T16:39:25.444Z
- open_remediation_tickets: 2
- known_reference_integrity_issues: 2

## Known Risks

- Repair follow-on remains incomplete: project-skill-bootstrap must still run: Repo-local skills still contain generic placeholder/model drift that must be regenerated with project-specific content.
- Historical completion should not be treated as fully trusted until pending process verification or explicit reverification is cleared.
- The workflow still records pending process verification even though no done tickets remain affected; clear the workflow flag before relying on a clean-state restart narrative.

## Next Action

project-skill-bootstrap must still run: Repo-local skills still contain generic placeholder/model drift that must be regenerated with project-specific content.
<!-- SCAFFORGE:START_HERE_BLOCK END -->
