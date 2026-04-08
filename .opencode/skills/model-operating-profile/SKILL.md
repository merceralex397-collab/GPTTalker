---
name: model-operating-profile
description: Shape GPTTalker prompts and delegation briefs for the selected MiniMax M2.7 evidence-first operating profile.
---

# Model Operating Profile

## Selected Runtime Profile

- Provider: `minimax-coding-plan`
- Team lead / planner / reviewers: `minimax-coding-plan/MiniMax-M2.7`
- Implementers: `minimax-coding-plan/MiniMax-M2.7`
- Utilities, docs, and QA helpers: `minimax-coding-plan/MiniMax-M2.7`
- Operating profile: `Specific-instruction evidence-first profile`

## Prompt Shape

Use short, bounded instructions with one clear goal. When the task touches workflow state, spell out the required proof and the legal next step.

Preferred structure:

```text
Goal
Constraints
Required evidence
Expected output
Blockers
```

## Repo-Specific Guidance

- Prefer direct file paths, exact commands, and concrete artifact names over narrative summaries.
- When routing stage work, name the owning specialist and the artifact they must produce.
- When asking for review or QA, require findings first and cite files, commands, or artifact paths.
- If the same lifecycle contradiction appears twice, stop and return a blocker instead of exploring alternate stage or status values.
- If a prerequisite is missing, say exactly which executable, config, or host assumption is absent.

## Output Bias

- Short, explicit sections beat broad prose.
- Example-shaped outputs help on this repo because workflow and artifact names are rigid.
- Never hide uncertainty behind a PASS or approval signal.
