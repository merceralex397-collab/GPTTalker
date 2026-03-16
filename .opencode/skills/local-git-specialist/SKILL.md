---
name: local-git-specialist
description: Follow GPTTalker's local-git workflow, branch naming, and commit conventions. Use when an agent needs to inspect history, create local commits, or reason about diff state.
---

# Local Git Specialist — GPTTalker

## When to Use

- Checking local status or diff state
- Preparing a local commit
- Verifying what changed for the current ticket
- Creating or switching branches

## Branch Naming Convention

Use descriptive kebab-case branches prefixed by category:

| Prefix | Use |
|---|---|
| `feat/` | New features (e.g., `feat/llm-bridge-adapter`) |
| `fix/` | Bug fixes (e.g., `fix/node-registry-timeout`) |
| `refactor/` | Refactoring without behavior change |
| `docs/` | Documentation-only changes |
| `test/` | Test additions or fixes |
| `chore/` | Tooling, CI, config changes |

If a ticket ID exists, include it: `feat/T-012-qdrant-hybrid-search`

## Commit Message Format

```
<type>(<scope>): <short summary>

<optional body — what and why, not how>

<optional ticket reference: Refs: T-012>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

**Scopes** (GPTTalker-specific):
- `hub` — hub server changes
- `node` — node agent changes
- `tools` — MCP tool handler changes
- `registry` — registry changes
- `context` — Qdrant/context pipeline changes
- `llm` — LLM bridge changes
- `shared` — shared model changes
- `deploy` — deployment/infra changes

Example:
```
feat(tools): add cross-repo search MCP tool

Implements semantic search across all indexed repos using Qdrant.
Returns ranked results with file paths and relevance scores.

Refs: T-015
```

## Rules

- Treat git work as local read/write unless the repo explicitly enables remote operations
- Do not assume GitHub APIs, PR automation, or remote pushes are available
- Keep commit scope aligned with the active ticket — one logical change per commit
- Use git state as supporting evidence, not as a substitute for ticket, workflow-state, or artifact updates
- Run `ruff check .` and `pytest` before committing
