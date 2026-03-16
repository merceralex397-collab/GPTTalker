---
description: Start the autonomous planning cycle for the current repo state
agent: gpttalker-team-leader
model: minimax-coding-plan/minimax-m2.5
---

Read the GPTTalker canonical project docs in this order:
1. `docs/spec/CANONICAL-BRIEF.md` — project definition and decisions
2. `AGENTS.md` — coding conventions and team structure
3. `tickets/BOARD.md` — work queue overview
4. `tickets/manifest.json` — active ticket

Resolve the active ticket and begin the internal lifecycle.

Rules:

- Treat this slash command as a human entrypoint only.
- Use agents, tools, plugins, and local skills for the internal autonomous cycle.
- Do not implement before a reviewed plan exists.
- Use `ticket_lookup`, `ticket_update`, and registered artifacts instead of raw file edits for stage control.
- Update ticket state and handoff artifacts as the cycle progresses.
