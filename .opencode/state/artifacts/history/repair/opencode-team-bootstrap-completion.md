# Repair Follow-On Completion

- completed_stage: opencode-team-bootstrap
- cycle_id: 2026-04-07T22:18:12Z
- completed_by: scafforge-repair

## Summary

Applied template-aligned fixes to 8 drifted agents (AGENT-001 through AGENT-008):

- `gpttalker-team-leader`: added `"explore": allow`; added Stop conditions, Advancement rules, Ticket ownership, Contradiction resolution sections; added bootstrap blocker detail rules; added blocked-status handling rules and managed_blocked detail rules; added stack-specific brief fields.
- `gpttalker-reviewer-code`: added `"review-audit-bridge": allow`; added compile bash entries; added compile/import check rules; updated description; added lease-blocked return rule.
- `gpttalker-reviewer-security`: added `"review-audit-bridge": allow`; updated description; added lease-blocked return rule.
- `gpttalker-tester-qa`: added `"review-audit-bridge": allow`; removed `ticket_update: allow`; updated description; added lease-blocked return rule and "do not advance ticket stage yourself" rule.
- `gpttalker-ticket-creator`: full replacement — added `ticket_reconcile: allow`; updated description; updated rules to support both `ticket_create` and `ticket_reconcile`.
- `gpttalker-planner`: added `"explore": allow`.
- `gpttalker-plan-review`: added lease-blocked return rule.
- `gpttalker-backlog-verifier`: added `smoke-test` to artifact reads; added lease-blocked return rule.

Evidence paths:
- `.opencode/agents/gpttalker-team-leader.md`
- `.opencode/agents/gpttalker-reviewer-code.md`
- `.opencode/agents/gpttalker-reviewer-security.md`
- `.opencode/agents/gpttalker-tester-qa.md`
- `.opencode/agents/gpttalker-ticket-creator.md`
- `.opencode/agents/gpttalker-planner.md`
- `.opencode/agents/gpttalker-plan-review.md`
- `.opencode/agents/gpttalker-backlog-verifier.md`
