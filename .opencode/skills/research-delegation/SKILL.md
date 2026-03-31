---
name: research-delegation
description: Delegate GPTTalker background research in a read-only way and preserve the useful output in repo-local evidence surfaces.
---

# Research Delegation

## Use This For

- Stack or provider reference gathering
- Cross-repo or architecture comparison
- Large diagnosis-pack review
- External docs that should inform a later ticket without mutating code

## Rules

- Keep delegated work read-only.
- Persist durable findings into `diagnosis/`, a stage artifact, or a restart surface before relying on them later.
- Convert unresolved research into blockers or follow-up tickets instead of treating it as settled.
- Do not use research delegation to bypass the ticket lifecycle or to perform hidden write work.
