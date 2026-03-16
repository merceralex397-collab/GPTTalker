---
description: Start the autonomous planning cycle for the current GPTTalker repo state
agent: gpttalker-team-leader
model: minimax-coding-plan/minimax-m2.5
---

Read the GPTTalker docs in this order:
1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `mcp_spec_pack/00-overview/00_project_brief.md`
5. `tickets/BOARD.md`
6. `tickets/manifest.json`

Resolve the active ticket and begin the internal lifecycle.

Rules:

- treat this slash command as a human entrypoint only
- use agents, tools, plugins, and local skills for the internal autonomous cycle
- do not implement before a reviewed plan exists
- use `ticket_lookup`, `ticket_update`, and registered artifacts instead of raw file edits for stage control
- update ticket state and handoff artifacts as the cycle progresses
