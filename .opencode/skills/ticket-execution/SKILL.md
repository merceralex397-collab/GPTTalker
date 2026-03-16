---
name: ticket-execution
description: Execute GPTTalker tickets through the required stage flow, artifact proofs, and implementer routing rules.
---

# Ticket Execution

Before using this guidance, call `skill_ping` with `skill_id: "ticket-execution"` and `scope: "project"`.

## Required stage order

1. planning
2. plan review
3. implementation
4. code review
5. security review when relevant
6. QA
7. docs and handoff
8. closeout

## Artifact expectations

- planning artifact: `.opencode/state/plans/<ticket>-planning-plan.md`
- implementation artifact: `.opencode/state/implementations/<ticket>-implementation-*.md`
- review artifact: `.opencode/state/reviews/<ticket>-review-*.md`
- QA artifact: `.opencode/state/qa/<ticket>-qa-*.md`
- handoff artifact when requested: `.opencode/state/handoffs/<ticket>-handoff-*.md`

## Implementer routing

- `repo-foundation`, `shared-runtime`, `storage`, `qa`, `docs`: `gpttalker-implementer`
- `hub-core`, `registry`, `security`, `repo-inspection`, `markdown`, `edge`: `gpttalker-implementer-hub`
- `node-agent`, `node-connectivity`: `gpttalker-implementer-node-agent`
- `llm-routing`, `context`, `cross-repo`, `scheduler`, `observability`: `gpttalker-implementer-context`

## Verification notes

- use `ticket_lookup` instead of reading status labels alone
- use `ticket_update` for active-ticket and workflow changes
- do not clear `pending_process_verification` unless `ticket_lookup.process_verification.affected_done_tickets` is empty
