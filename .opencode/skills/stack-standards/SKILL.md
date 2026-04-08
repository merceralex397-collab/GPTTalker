---
name: stack-standards
description: Apply GPTTalker's actual Python, FastAPI, SQLite, Qdrant, httpx, logging, and validation conventions when changing code or review expectations.
---

# Stack Standards

## Stack Summary

- Python `3.11+`
- FastAPI for hub and node-agent HTTP surfaces
- Pydantic models for request and response schemas
- SQLite via `aiosqlite` for structured runtime state
- Qdrant via `qdrant-client` for semantic project context
- `httpx.AsyncClient` with explicit timeouts for outbound HTTP
- ngrok for the public edge, Tailscale for internal transport
- `pytest`, `pytest-asyncio`, and `ruff` for validation

## Python And API Rules

- Use type hints on functions, return values, and non-obvious locals.
- Prefer `str | None` over `Optional[str]`.
- Keep async paths fully async. Do not introduce synchronous sqlite access inside FastAPI or service code.
- Use Pydantic models for tool contracts and service boundaries.
- FastAPI endpoints must be `async def`.
- Use `fastapi.Depends` for dependency injection. For app-state access in dependencies, use `request: Request`, not `app: FastAPI`.
- If a runtime annotation would evaluate a TYPE_CHECKING-only symbol, use a string annotation instead.

## Storage And Context Rules

- Shared runtime state belongs in `src/shared/` repositories and helpers.
- Schema and repository changes must preserve the existing async `aiosqlite` pattern.
- Qdrant changes must preserve provenance metadata, content-hash tracking, and repo access boundaries.

## Networking And Security Rules

- Every outbound `httpx` call needs an explicit timeout.
- Treat Tailscale as the only trusted internal transport boundary.
- Keep ngrok-specific logic isolated to hub config, startup, and service layers instead of spreading provider assumptions across unrelated modules.
- Fail closed on unknown nodes, repos, write targets, and service aliases.
- Normalize user-controlled paths and reject traversal, symlink escape, and out-of-root writes.

## Logging Rules

- Use structured logging helpers from `src/shared/logging.py`.
- Log tool flows with trace-aware metadata and redaction intact.
- Never add bare `print()` calls.

## Validation Commands

- Bootstrap: `UV_CACHE_DIR=/tmp/uv-cache uv sync --locked --extra dev`
- Lint: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- Full tests: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short`
- Import smoke:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"`
  - `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"`
- Targeted scripts:
  - `gpttalker-lint`
  - `gpttalker-test`
  - `gpttalker-validate`

## Testing Expectations

- Every MCP tool handler needs at least one happy-path and one error-path test.
- Use `pytest-asyncio` patterns for async behavior.
- Treat missing host prerequisites such as `uv`, `pytest`, `rg`, or git identity as blockers, not as excuses to manufacture PASS evidence.
- When import or startup behavior changes, include runtime import proof, not just static lint output.

## Review Focus

- FastAPI dependency wiring and runtime-safe annotations
- Path validation and fail-closed behavior
- SQLite commit behavior and async boundaries
- ngrok edge assumptions leaking outside edge-specific modules
- Logging redaction, trace propagation, and audit metadata
