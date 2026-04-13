---
name: stack-standards
description: Apply GPTTalker-specific Python, FastAPI, MCP, policy, validation, and runtime conventions when planning, implementing, reviewing, or testing repository work.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

GPTTalker is a Python 3.11+ FastAPI MCP hub with a lightweight Python node-agent service. It uses SQLite for structured state, Qdrant for semantic context, Tailscale for private hub-to-node transport, and ngrok for the public HTTPS MCP edge. The repo is security-sensitive: unknown nodes, repos, services, paths, and write targets must fail closed.

## Core Stack

- Runtime: Python 3.11+, FastAPI, uvicorn.
- Package metadata: `pyproject.toml`.
- Package manager: prefer `uv`; use `UV_CACHE_DIR=/tmp/uv-cache` for repeatable host runs.
- Hub package: `src/hub/`.
- Node-agent package: `src/node_agent/`.
- Shared schemas, config, repositories, and migrations: `src/shared/`.
- Tests: `tests/`.
- Linting and formatting: ruff.
- Test runner: pytest with `asyncio_mode = "auto"`.

## Validation Commands

Use the narrowest command that proves the touched surface. For review, QA, and remediation closeout, record the exact command, raw output, and explicit PASS/FAIL result.

- Install/update dev environment: `UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev`.
- Lint: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`.
- Format check: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check .`.
- Test collection: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest --collect-only tests/ -q`.
- Fast failure test run: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short`.
- Hub import check: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app; print(app.title)"`.
- Node-agent import check: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app; print(app.title)"`.
- Make targets are available as convenience wrappers: `make lint`, `make test`, and `make validate`.

If `uv` is unavailable, report a host-prerequisite blocker instead of silently switching to an unrecorded environment. Use `python3` where a direct interpreter is needed.

## FastAPI Rules

- Keep route handlers thin. Put policy, routing, persistence, and service logic in `src/hub/services/`, `src/hub/policy/`, `src/hub/tools/`, or `src/node_agent/` as appropriate.
- Use FastAPI dependency injection deliberately. Dependency functions that need application state should accept `request: Request` and read `request.app.state`; do not type a dependency parameter as `FastAPI`.
- When a type is imported only under `TYPE_CHECKING`, use a string annotation such as `-> "TypeName"` so runtime imports remain valid.
- Validate external payloads at the boundary with Pydantic models or explicit checks before policy or filesystem operations run.
- Return structured errors for policy denials and unsupported targets; do not expose secret values, raw environment, or unrestricted filesystem paths in error text.

## Security And Policy

- Default deny is the project rule. Unknown repo aliases, node aliases, service aliases, write targets, path roots, and scopes must be rejected.
- Normalize and validate paths before reading or writing. Preserve traversal prevention and approved write-root checks.
- Markdown delivery must stay scoped to approved write targets, allowed extensions, and atomic writes.
- Keep Tailscale internal traffic and ngrok public edge concerns separate. Do not reintroduce Cloudflare Tunnel assumptions after the ngrok pivot.
- Do not log API keys, Tailscale identifiers beyond approved aliases, ngrok tokens, model credentials, or generated secret-bearing docs.
- Direct git commit and push actions remain out of scope; inspection and status operations are allowed only through approved tool contracts.

## MCP And Tool Contracts

- MCP-facing tools should return predictable structured data, not console-oriented prose.
- Tool handlers must enforce policy before performing filesystem, network, model, or registry actions.
- Repo inspection tools should prefer `rg` for text search and git CLI for status/history.
- LLM routing must go through approved aliases, model registry, scheduler policy, and health checks.
- Node-agent operations must be scoped and auditable; no unrestricted shell execution.
- Observability paths should preserve task IDs, trace IDs, timestamps, target aliases, outcome, and failure reason.

## Persistence

- SQLite owns registry, task, generated-doc, issue, and relationship history.
- Qdrant owns semantic project-context vectors.
- Migrations must be explicit and idempotent; do not hide schema mutation in request handlers.
- Runtime state must persist across restarts unless a ticket explicitly owns a temporary or cache-only surface.

## Testing Expectations

- Policy-denial tests are as important as happy-path tests.
- Add focused tests for new tool contracts, path validation, alias routing, migration behavior, and serialization boundaries.
- For bug fixes, include a regression check that would have failed before the fix.
- Treat import failures as critical execution findings. Before approving dependency, route, or typing changes, run the hub and node-agent import checks above.

## Ticket And Remediation Rules

- Use the ticket tools and lifecycle state. Do not hand-advance stage or status fields.
- Stage order is `planning -> plan_review -> implementation -> review -> qa -> smoke-test -> closeout`.
- Read `ticket_lookup.transition_guidance` before calling `ticket_update`.
- `smoke_test` is the only legal producer of smoke-test artifacts.
- If a remediation ticket carries `finding_source`, its review artifact must rerun the original finding-producing command or the canonical acceptance command, include raw command output, and state PASS or FAIL before closeout can be trusted.
- Missing tools, blocked services, or invalid host prerequisites are blockers to record, not reasons to manufacture PASS evidence.
