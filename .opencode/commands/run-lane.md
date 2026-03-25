---
description: Run one bounded write-capable lane through the lease-based workflow
agent: gpttalker-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Choose one ready ticket lane, claim the required lease, delegate bounded implementation, then return control to the team leader for synthesis.

Rules:

- Treat this slash command as a human entrypoint only.
- Use `ticket_claim` and `ticket_release` for write-capable lane ownership.
- Prefer `gpttalker-lane-executor` for bounded parallel implementation.
- Do not overlap write-capable work across lanes with conflicting paths or dependencies.
