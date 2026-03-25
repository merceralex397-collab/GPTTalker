---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack: `Python 3.11+ + FastAPI + SQLite + Qdrant`

Language and framework rules:

- use Python 3.11+ syntax and full type hints on public functions, return values, and non-obvious variables
- use `str | None` instead of `Optional[str]`
- FastAPI endpoints must be `async def`
- request and response payloads must use Pydantic models
- dependency injection should use `fastapi.Depends`
- in dependency helpers, use `request: Request` and read shared state from `request.app.state`; do not inject `app: FastAPI` directly

Storage and networking rules:

- use `aiosqlite` for structured runtime state; do not call synchronous sqlite APIs from async paths
- use Qdrant for semantic context storage
- use async `httpx` with explicit timeouts for outbound hub or node-agent calls
- treat Tailscale as the internal transport boundary

Validation rules:

- run `ruff check .` for linting
- run `pytest tests/ --collect-only -q --tb=no` before treating Python QA evidence as credible
- run `pytest tests/ -q --tb=no` for the full suite when the ticket changes executable Python behavior
- every MCP tool handler should keep one happy-path and one error-path test

Implementation rules:

- use structured logging, not `print()`
- redact secrets, tokens, passwords, and raw file contents from logs
- log tool calls with `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, and `duration_ms`
- fail closed on unknown nodes, repos, write targets, and service aliases
