# GPTTalker Agent Rules

This file is the project-local instruction source for GPTTalker.

If this file conflicts with any global AI instruction file, **this file wins** for this repo.

## Coding Conventions — Python + FastAPI

### Language and Types

- **Python 3.11+** minimum. Use modern syntax where it improves clarity.
- Use **type hints everywhere**: function signatures, return types, and non-obvious variables.
- Prefer `str | None` over `Optional[str]`.

### API and Data Models

- Use **Pydantic models** for all API request and response schemas.
- Use **async/await** for all FastAPI endpoints.
- Use `fastapi.Depends` for dependency injection.

### Database and Context Storage

- Use **SQLite via aiosqlite** for structured runtime state.
- Use **Qdrant** for semantic project context.
- Never use synchronous sqlite APIs in async paths.

### HTTP and Networking

- Use **httpx** (async) for all outbound hub and node-agent HTTP.
- Set explicit timeouts on every httpx call.
- Treat **Tailscale** as the only internal transport boundary.

### Validation and Testing

- Use **ruff** for linting and formatting.
- Use **pytest** for validation and `pytest-asyncio` for async cases.
- Every MCP tool handler must have at least one happy-path and one error-path test.

### Logging and Security

- Use structured logging. No bare `print()` statements.
- Log tool calls with `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, and `duration_ms`.
- Redact secrets, tokens, passwords, and raw file contents from logs.
- Fail closed on unknown nodes, repos, write targets, and service aliases.

## Truth Hierarchy

| Kind of state | Owner file | Notes |
|---|---|---|
| Immutable pre-generation source pack | `mcp_spec_pack/` | Preserved reference material; do not rewrite |
| Project definition | `docs/spec/CANONICAL-BRIEF.md` | Durable facts, constraints, and accepted decisions |
| Work queue (machine) | `tickets/manifest.json` | Machine-readable routing source |
| Work queue (human) | `tickets/BOARD.md` | Derived queue board |
| Active ticket / stage | `.opencode/state/workflow-state.json` | Transient workflow and process-version state |
| Artifact registry | `.opencode/state/artifacts/registry.json` | Cross-stage artifact metadata |
| Bootstrap provenance | `.opencode/meta/bootstrap-provenance.json` | Scaffold and retrofit history |
| Agent prompts | `.opencode/agents/*.md` | Repo-local agent prompts |
| Agent team overview | `AGENTS.md` | Team, conventions, security, and workflow rules |
| Process workflow | `docs/process/workflow.md` | Stage and proof contract |
| Handoff / resume | `START-HERE.md` | Derived restart surface |
| Hub runtime config | `src/hub/config/` | Future runtime configuration |
| Node registry | SQLite `nodes` table | Runtime state |
| Repo registry | SQLite `repos` table | Runtime state |
| Task history | SQLite `tasks` table | Runtime audit trail |
| Project context vectors | Qdrant collections | Runtime semantic memory |

## Operating Priorities

1. Read `START-HERE.md` first.
2. Treat `docs/spec/CANONICAL-BRIEF.md` as the canonical project summary.
3. Use `mcp_spec_pack/` when generated docs need source-pack verification.
4. Use `tickets/manifest.json` as the machine-readable work queue.
5. Use `.opencode/state/workflow-state.json` for transient approval and process-version state.
6. Treat the stage-specific artifact directories as canonical proof bodies.
7. Keep the repo signposted and deterministic for weaker models.
8. Follow the internal stage gates: plan -> review -> implement -> review -> QA -> closeout.

## Required Read Order

1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `mcp_spec_pack/00-overview/00_project_brief.md`
5. `docs/process/workflow.md`
6. `docs/process/agent-catalog.md`
7. `docs/process/model-matrix.md`
8. `docs/process/git-capability.md`
9. `tickets/README.md`
10. `tickets/manifest.json`
11. `tickets/BOARD.md`

## Agent Team

### Visible Entrypoint

| Agent | Role | Scope |
|---|---|---|
| `gpttalker-team-leader` | Main orchestrator | Resolves ticket state, routes stages, and synthesizes closeout. |

### Core Specialists (hidden)

| Agent | Role | Scope |
|---|---|---|
| `gpttalker-planner` | Planning and task breakdown | Produces decision-complete plans for one ticket. |
| `gpttalker-plan-review` | Plan validation | Reviews plans for completeness, feasibility, and spec alignment. |
| `gpttalker-implementer` | Cross-cutting implementation | Handles shared workflow/tooling or cross-domain implementation work. |
| `gpttalker-implementer-hub` | Hub implementation | FastAPI hub server, MCP tool handlers, policy engine, registries, edge integration. |
| `gpttalker-implementer-node-agent` | Node agent implementation | Per-machine service, local repo executors, write delivery, health checks. |
| `gpttalker-implementer-context` | Context implementation | Qdrant, indexing, project context, cross-repo intelligence, scheduler/context pipelines. |
| `gpttalker-reviewer-code` | Code review | Reviews correctness, regressions, and validation completeness. |
| `gpttalker-reviewer-security` | Security review | Reviews trust boundaries, secrets, access controls, and redaction. |
| `gpttalker-tester-qa` | Testing and QA | Runs validation and determines closeout readiness. |
| `gpttalker-docs-handoff` | Documentation and handoff | Updates restart surfaces and closeout docs. |
| `gpttalker-backlog-verifier` | Post-migration verification | Re-checks previously completed work after workflow changes. |
| `gpttalker-ticket-creator` | Guarded follow-up creation | Creates migration follow-up tickets only from verifier-backed proof. |

### Utility Specialists (hidden)

| Agent | Role | Scope |
|---|---|---|
| `gpttalker-utility-explore` | Exploration and discovery | Reads files, searches code, and gathers repo evidence. |
| `gpttalker-utility-shell-inspect` | System inspection | Runs read-only shell diagnostics. |
| `gpttalker-utility-summarize` | Summarization | Condenses large outputs or source packs. |
| `gpttalker-utility-ticket-audit` | Ticket/state audit | Audits ticket and workflow consistency. |
| `gpttalker-utility-github-research` | GitHub research | Searches GitHub for references and prior art. |
| `gpttalker-utility-web-research` | Web research | Fetches external documentation and references. |

## Security Rules

1. **No secrets in code.** Use environment variables or ignored config files.
2. **No unrestricted shell access.** GPTTalker exposes bounded tool handlers, not general shell control.
3. **All paths normalized.** Reject `..`, symlink escapes, and absolute user-supplied paths.
4. **Redact logs.** Never log raw secrets or large file contents.
5. **Default deny.** Unknown nodes, repos, write targets, and LLM aliases are rejected.
6. **Fail closed.** Validation or policy failures return structured errors.
7. **Atomic writes only.** `write_markdown` and similar write paths must write-to-temp then rename.
8. **Audit everything.** Persist tool-call metadata and task history.

## Workflow Rules

- Keep queue status coarse: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`.
- Keep plan approval in workflow state and artifacts, not in ticket status.
- Treat `tickets/BOARD.md` as a derived human view, not a second state machine.
- Use ticket tools and workflow state instead of raw file edits for stage transitions.
- Use `parallel_safe` and `overlap_risk` to decide whether multiple tickets may advance together.
- Use `.opencode/meta/bootstrap-provenance.json` as the canonical process-contract record.
- Only create migration follow-up tickets from backlog-verifier findings during an active verification window.
- Keep `START-HERE.md`, `tickets/BOARD.md`, and `tickets/manifest.json` aligned with the canonical sources that feed them.
