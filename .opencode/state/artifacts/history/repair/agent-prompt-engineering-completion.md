# Repair Follow-On Completion

- completed_stage: agent-prompt-engineering
- cycle_id: 2026-04-07T22:18:12Z
- completed_by: scafforge-repair

## Summary

Applied prompt hardening across all 8 drifted agents as part of the same repair pass:

- Team leader: added contradiction resolution rules, advancement rules with verdict checking, stop conditions to prevent doom loops, and managed_blocked detail rules that surface exact repair instructions to the operator.
- Reviewer agents (code, security): added `review-audit-bridge` skill delegation to enforce consistent output ordering and blocker rules.
- Tester QA: added `review-audit-bridge` skill delegation; removed direct ticket_update authority; added explicit "do not advance ticket stage yourself" constraint to enforce team-leader-only advancement.
- Ticket creator: updated from single-path `ticket_create` to full `ticket_create` + `ticket_reconcile` router, enabling lineage reconciliation as well as creation.
- All non-team-leader specialists: added lease-blocked return rule so specialists return blockers to the team leader instead of attempting to claim leases themselves.

Evidence paths:
- `.opencode/agents/gpttalker-team-leader.md`
- `.opencode/agents/gpttalker-reviewer-code.md`
- `.opencode/agents/gpttalker-reviewer-security.md`
- `.opencode/agents/gpttalker-tester-qa.md`
- `.opencode/agents/gpttalker-ticket-creator.md`
- `.opencode/agents/gpttalker-plan-review.md`
- `.opencode/agents/gpttalker-backlog-verifier.md`
- `.opencode/agents/gpttalker-planner.md`
