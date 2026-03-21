---
description: Resume the current autonomous cycle using the latest repo state
agent: gpttalker-team-leader
model: minimax-coding-plan/MiniMax-M2.5
---

Resume from `START-HERE.md`, `tickets/manifest.json`, `.opencode/state/workflow-state.json`, and `.opencode/state/context-snapshot.md` if it exists.

Rules:

- Reconfirm the active ticket and stage.
- Reconfirm the process-version state and whether post-migration verification is pending.
- Regenerate a short context snapshot if the state looks stale.
- Reconfirm the required artifact proof for the next stage before continuing.
- Continue the required internal stage sequence instead of skipping ahead.
