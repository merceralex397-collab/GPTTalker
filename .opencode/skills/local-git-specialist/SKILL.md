---
name: local-git-specialist
description: Use GPTTalker's local-git workflow safely for diff inspection, local commits, and ticket-scoped history checks.
---

# Local Git Specialist

## Scope

- local status, diff, blame, and history inspection
- local commits when the active ticket is actually ready
- validation steps that rely on repo history

## Rules

- Treat git state as supporting evidence, not as canonical workflow state.
- Keep commit scope aligned with the active ticket only.
- Do not assume GitHub APIs, PR automation, or remote pushes.
- If git identity is missing and a validation depends on commit creation, record an environment blocker instead of blaming product code.
- Avoid destructive git operations unless the user explicitly asks for them.
