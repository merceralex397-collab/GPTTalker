---
name: model-operating-profile
description: Apply the `Specific-instruction evidence-first profile` operating profile for the selected downstream models. Use when shaping prompts, delegation briefs, review asks, or evidence requests for this repo.
---

# Model Operating Profile

Before reading anything else, call `skill_ping` with `skill_id: "model-operating-profile"` and `scope: "project"`.

Selected runtime profile:

- provider: `minimax-coding-plan`
- team lead / planner / reviewers: `minimax-coding-plan/MiniMax-M2.7`
- implementer: `minimax-coding-plan/MiniMax-M2.7`
- utilities, docs, and QA helpers: `minimax-coding-plan/MiniMax-M2.7`
- operating profile: `Specific-instruction evidence-first profile`

Use this profile when drafting:

- task prompts
- delegation briefs
- review requests
- handoff expectations

Profile guidance:

`Apply explicit, example-shaped, bounded instructions for the selected downstream models. Prefer direct evidence and concrete task framing over broad summaries.`

Required rules:

- prefer clear and specific instructions
- state the purpose or why when it reduces ambiguity
- use example-shaped outputs when they make the expected shape concrete
- focus on one bounded goal at a time instead of broad parallel asks
- prefer direct evidence, command output, and cited repo surfaces over summaries
- stop on blockers instead of guessing or silently filling gaps

When ambiguity is likely, prefer a concrete output shape such as:

```text
Goal
Constraints
Expected output
Evidence required
Blockers
```
