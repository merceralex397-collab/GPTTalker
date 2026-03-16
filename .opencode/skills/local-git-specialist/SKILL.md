---
name: local-git-specialist
description: Apply GPTTalker’s local git hygiene rules for diff inspection, commit preparation, and safe non-destructive history use.
---

# Local Git Specialist

Before using this guidance, call `skill_ping` with `skill_id: "local-git-specialist"` and `scope: "project"`.

## Rules

- local git only; do not assume remote push, PR creation, or merge automation
- inspect `git status` and `git diff` before and after ticket work
- never use destructive cleanup commands unless explicitly approved by the user
- keep commits aligned with a single ticket when possible
