# GPTTalker Agent Rules

This file is the project-local instruction source for GPTTalker.

If this file conflicts with any global AI instruction file, **this file wins** for this repo.

## Coding Conventions — Python + FastAPI

### Language and Types

- **Python 3.11+** minimum. Use modern syntax (`match`, `type` aliases, `ExceptionGroup` where appropriate).
- Use **type hints everywhere**: function signatures, return types, variable annotations for non-obvious types.
- Prefer `str | None` over `Optional[str]`.

### API and Data Models

- Use **Pydantic models** for all API request/response schemas. No raw dicts crossing API boundaries.
- Use **async/await** for all FastAPI endpoints. No sync handlers.
- Use `fastapi.Depends` for dependency injection (DB sessions, auth, policy checks).

### Database

- Use **SQLite via aiosqlite** for all async DB access (node registry, repo registry, task history).
- Never use synchronous sqlite3 in async code paths.

### HTTP

- Use **httpx** (async) for all outbound HTTP: hub → node agents, hub → LLM backends, hub → Qdrant.
- Set explicit timeouts on all httpx calls. No open-ended waits.

### Linting and Testing

- Use **ruff** for linting and formatting. Run `ruff check` and `ruff format --check` in CI.
- Use **pytest** for all tests. Use `pytest-asyncio` for async test cases.
- Every MCP tool handler must have at least one happy-path and one error-path test.

### Logging

- Use **structured logging** (structlog or equivalent). No bare `print()` statements.
- All MCP tool calls must be logged with: `trace_id`, `tool_name`, `target_node`, `target_repo` (where applicable), `caller`, `outcome`, `duration_ms`.
- Redact secrets, tokens, and file contents from log output.

### MCP Tool Handler Rules

- All tool handlers **must validate inputs** against registered targets (nodes, repos, write targets).
- **Fail closed** on unknown targets — return an error, never silently proceed.
- All paths must be **normalized** before use (no `..`, no symlink escapes, no absolute paths accepted from callers).
- Tool handlers must be idempotent where possible. `write_markdown` uses atomic writes with content hashing.

### General Style

- Keep functions short and focused. One function, one responsibility.
- Prefer explicit over clever. This codebase must be readable by weaker models.
- Comment only when the "why" is non-obvious. Do not restate what the code does.
- Use constants or enums for magic strings (tool names, status values, service kinds).

## Truth Hierarchy

The canonical truth map for GPTTalker. When sources conflict, the higher-ranked source wins.

| Kind of state | Owner file | Notes |
|---|---|---|
| Project definition | `docs/spec/CANONICAL-BRIEF.md` | Durable facts, constraints, decisions |
| Work queue (machine) | `tickets/manifest.json` | Machine-readable queue state |
| Work queue (human) | `tickets/BOARD.md` | Derived view — never edit directly |
| Active ticket / stage | `.opencode/state/workflow-state.json` | Transient approval state |
| Artifact registry | `.opencode/state/artifacts/registry.json` | Cross-stage artifact metadata |
| Bootstrap provenance | `.opencode/meta/bootstrap-provenance.json` | How scaffold was generated/repaired |
| Agent prompts | `.opencode/agents/*.md` | Individual agent system prompts |
| Agent team overview | `AGENTS.md` (this file) | Conventions, team, security |
| Process workflow | `docs/process/workflow.md` | Stage gates and procedures |
| Handoff / resume | `START-HERE.md` | Derived restart surface |
| Hub runtime config | `src/hub/config/` | Runtime configuration files |
| Node registry | SQLite `nodes` table | Runtime — managed by hub |
| Repo registry | SQLite `repos` table | Runtime — managed by hub |
| Task history | SQLite `tasks` table | Runtime — audit trail |
| Project context vectors | Qdrant collections | Runtime — semantic memory |

## Operating Priorities

1. Read `START-HERE.md` first.
2. Treat `docs/spec/CANONICAL-BRIEF.md` as the project source of truth.
3. Use `tickets/manifest.json` as the machine-readable work queue.
4. Use `.opencode/state/workflow-state.json` for transient stage approval state.
5. Treat the stage-specific artifact directories as the canonical stage-proof body locations.
6. Keep the repo signposted and deterministic for weaker models.
7. Follow the internal stage gates: plan → review → implement → review → QA → closeout.

## Required Read Order

1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `docs/process/workflow.md`
5. `docs/process/agent-catalog.md`
6. `docs/process/model-matrix.md`
7. `docs/process/git-capability.md`
8. `tickets/README.md`
9. `tickets/manifest.json`
10. `tickets/BOARD.md`

## Agent Team

### Visible Entrypoint

| Agent | Role | Scope |
|---|---|---|
| `gpttalker-team-leader` | Main orchestrator | Advances stages via ticket tools and workflow state. Only agent visible to external callers. |

### Core Specialists (hidden)

| Agent | Role | Scope |
|---|---|---|
| `gpttalker-planner` | Planning and task breakdown | Produces structured plans from tickets. Writes to `.opencode/state/plans/`. |
| `gpttalker-plan-review` | Plan validation | Reviews plans for completeness, feasibility, and spec alignment. Read-only — returns findings. |
| `gpttalker-implementer-hub` | Hub implementation | Implements hub server code: FastAPI app, tool handlers, policy engine, context manager. |
| `gpttalker-implementer-node-agent` | Node agent implementation | Implements node agent service: executors, health checks, registration. |
| `gpttalker-implementer-context` | Context/Qdrant implementation | Implements Qdrant integration, semantic indexing, project context tools. |
| `gpttalker-reviewer-code` | Code review | Reviews implementations for correctness, style, and convention compliance. Read-only. |
| `gpttalker-reviewer-security` | Security review | Reviews for secrets in code, path traversal, unrestricted access, log redaction. Read-only. |
| `gpttalker-tester-qa` | Testing and QA | Writes and runs tests. Validates tool handlers against spec. |
| `gpttalker-docs-handoff` | Documentation and handoff | Updates START-HERE.md, README.md, and inline docs. Produces handoff artifacts. |

### Utility Specialists (hidden)

| Agent | Role | Scope |
|---|---|---|
| `gpttalker-utility-explore` | Exploration and discovery | Reads files, searches code, answers codebase questions. Read-only. |
| `gpttalker-utility-shell-inspect` | System inspection | Runs diagnostic commands. Read-only. |
| `gpttalker-utility-summarize` | Text summarization | Condenses large outputs. Read-only. |
| `gpttalker-utility-ticket-audit` | Ticket and history analysis | Audits ticket state, artifact alignment. Read-only. |
| `gpttalker-utility-github-research` | GitHub research | Searches GitHub for references, issues, prior art. Read-only. |
| `gpttalker-utility-web-research` | Web research | Fetches external documentation and references. Read-only. |

### Agent Workflow Constraints

- Team leader advances stages through ticket tools and workflow state, not manual file editing.
- Each major stage must leave a canonical artifact before the next stage begins.
- Read-only specialists return findings instead of mutating files.
- Every substantive change must map to a ticket.
- Do not implement before an approved plan exists.

## Security Rules

1. **No secrets in code.** Tokens, API keys, passwords, and credentials must live in environment variables or config files excluded from version control. Never hardcode secrets.
2. **No unrestricted shell access.** GPTTalker never exposes raw shell execution to ChatGPT. Node agents execute only predefined operations (file read, git, ripgrep, LLM call).
3. **All paths normalized.** Every file path received from a caller must be normalized and validated before use. Reject paths containing `..`, symlink escapes, or absolute paths. Confine all operations to registered repo roots.
4. **Redaction in logs.** Structured logs must redact: file contents beyond a size threshold, API keys, bearer tokens, passwords, and any field marked sensitive in Pydantic models. Log metadata (trace ID, tool name, target, outcome, duration) — not payloads.
5. **Default deny.** Unknown nodes, repos, write targets, and LLM service aliases are rejected. The hub never forwards a request to an unregistered target.
6. **Fail closed.** On validation failure, policy violation, or unexpected error, return a structured error to the caller. Never silently drop, retry, or fall through to a permissive path.
7. **Atomic writes only.** `write_markdown` writes to a temp file and renames. No partial writes. Content hash returned for verification.
8. **Audit everything.** Every tool call is logged with timestamp, caller, target, outcome, and trace ID. Task history is persisted in SQLite.

## Workflow Rules

- Keep queue status coarse: `todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `done`.
- Keep plan approval in workflow state and artifacts, not in ticket status.
- Treat `tickets/BOARD.md` as a derived human view, not a second state machine.
- Use ticket tools and workflow-state instead of raw file edits for stage transitions.
- Keep `START-HERE.md`, `tickets/BOARD.md`, and `tickets/manifest.json` aligned with the canonical sources that feed them.
