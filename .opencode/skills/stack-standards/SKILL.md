---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

GPTTalker stack: **Python 3.11+ · FastAPI · aiosqlite · Qdrant · httpx · Tailscale · Cloudflare Tunnel · pytest · ruff**

## Language and Types

- Python 3.11+ minimum. Use modern syntax where it improves clarity.
- Use type hints everywhere: function signatures, return types, and non-obvious variables.
- Prefer `str | None` over `Optional[str]`.
- Use `from __future__ import annotations` only when cyclic imports require it.

## API and Data Models

- Use **Pydantic v2 models** for all FastAPI request and response schemas.
- Use `async/await` for all FastAPI endpoint handlers.
- Use `fastapi.Depends` for dependency injection; never import service objects at module scope for testing purposes.
- Validate all external inputs at the API boundary; never pass raw request data into internal service layers unvalidated.

## Database

- Use **aiosqlite** for structured runtime state (nodes, repos, tasks, leases).
- Never use synchronous sqlite3 APIs in async paths.
- Always use parameterised queries; never construct SQL strings by concatenation.
- Migrations must be idempotent `CREATE TABLE IF NOT EXISTS` or `ALTER TABLE` patterns.

## Context Storage

- Use **Qdrant** for semantic project context and cross-repo intelligence.
- Collection names must be scoped per-repo to prevent cross-repo bleed.

## HTTP and Networking

- Use **httpx** (async) for all outbound hub and node-agent HTTP calls.
- Set explicit `timeout=httpx.Timeout(...)` on every httpx call; never rely on the default.
- Treat **Tailscale** as the only trusted internal transport boundary; all node-agent communication must traverse Tailscale.
- Public edge traffic routes through **Cloudflare Tunnel**; do not expose internal ports directly.

## Validation and Testing

- Use **ruff** for linting (`ruff check .`) and formatting (`ruff format .`).
- Use **pytest** for all tests; use **pytest-asyncio** for async test cases.
- Every MCP tool handler must have at least one happy-path and one error-path test.
- Run `uv run pytest tests/ --collect-only -q --tb=no` before the full suite to verify collection.
- Run `uv run pytest` for the full suite; `uv run pytest tests/<module>` for targeted runs.
- Import-check command: `uv run python -c "from src.hub.main import app; from src.node_agent.main import app"`.
- Compile-check command: `python3 -m py_compile $(find src -name '*.py')`.

## Quality Gate Commands

Run in this order for review and QA stages:

```sh
ruff check .
ruff format --check .
python3 -m py_compile $(find src -name '*.py')
uv run pytest tests/ --collect-only -q --tb=no
uv run pytest --tb=short -q
```

## Logging and Security

- Use **structured logging** (stdlib `logging` with a JSON formatter or equivalent); no bare `print()` statements.
- Log tool calls with: `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, `duration_ms`.
- Redact secrets, tokens, passwords, and raw file contents from all log output.
- Use environment variables or ignored config files for all secrets; never commit secrets to source.
- Fail closed on unknown nodes, repos, write targets, and service aliases.
- All path inputs must be normalised; reject `..`, symlink escapes, and absolute user-supplied paths.
- Atomic writes only: write to a temp file, then rename into place.
- Validation or policy failures must return structured errors, not silent fallthrough.

## Process

- Use ticket tools to track work; do not silently advance stages without updating ticket state.
- Artifacts produced by each stage must be registered via `artifact_write` / `artifact_register`.
- Smoke tests run against the real service or module entrypoint, not a mocked surrogate.
- Coordinator-authored QA or smoke-test artifacts are invalid proof; route those stages through the assigned specialist or tool.
