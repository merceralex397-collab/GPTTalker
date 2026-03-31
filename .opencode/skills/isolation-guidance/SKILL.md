---
name: isolation-guidance
description: Decide when GPTTalker work should move into a safer isolated lane such as a worktree or sandbox instead of editing the shared workspace directly.
---

# Isolation Guidance

## Use Isolation When

- a ticket will touch both hub and node-agent runtime paths at once
- long-running validation or repair work could destabilize the current workspace
- multiple write-capable lanes would otherwise overlap in the same files

## Rules

- Prefer the lightest isolation that actually reduces collision risk.
- Keep canonical ticket, workflow, and artifact state in the main repo surfaces even if code work happens elsewhere.
- If safe isolation is required but unavailable, return a blocker instead of improvising an unsafe parallel run.
