---
description: Resume the current GPTTalker autonomous cycle from the latest repo state
agent: gpttalker-team-leader
model: minimax-coding-plan/minimax-m2.5
---

Resume from `START-HERE.md`, `tickets/manifest.json`, `.opencode/state/workflow-state.json`, and `.opencode/state/context-snapshot.md` if it exists.

Rules:

- reconfirm the active ticket, stage, and process-verification state
- regenerate a short context snapshot if the state looks stale
- reconfirm the required artifact proof for the next stage before continuing
- continue the required stage sequence instead of skipping ahead
