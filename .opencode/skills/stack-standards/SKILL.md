---
name: stack-standards
description: Enforce GPTTalker's Python + FastAPI engineering standards. Use when planning or implementing work to ensure correct language features, framework patterns, validation, testing, and tooling conventions.
---

# Stack Standards — GPTTalker

## Language & Runtime

- **Python 3.11+** — use modern syntax (match/case, `type` aliases, `ExceptionGroup` when appropriate)
- **Full type hints everywhere** — all function signatures, return types, and variable annotations where non-obvious
- No `Any` unless genuinely unavoidable; prefer `Union`, `TypeVar`, or protocol types

## Framework — FastAPI

- All endpoints are **async** (`async def`)
- Use **Pydantic v2** models for all request bodies, response models, and internal data structures
- Define response models explicitly on route decorators: `@router.post("/foo", response_model=FooResponse)`
- Use `Depends()` for dependency injection (DB sessions, auth, registries)
- Use `HTTPException` with appropriate status codes; never return bare dicts for errors

## Database — SQLite via aiosqlite

- All database access through **aiosqlite** (async)
- Use parameterized queries exclusively — never string-interpolate SQL
- Migrations managed explicitly (SQL files or a lightweight migration tool)
- Connection pooling via a shared async context manager

## HTTP Client — httpx

- All outbound HTTP (hub-to-node, hub-to-LLM) uses **httpx.AsyncClient**
- Set explicit timeouts on every request
- Use connection pooling (shared client instances, not per-request)
- Hub-to-node communication always goes over Tailscale addresses

## Vector Store — qdrant-client

- Use the async Qdrant client (`qdrant_client.async_qdrant_client`)
- Collection naming: one collection per indexed repo, plus a global cross-repo collection
- Always include metadata payloads (repo, file path, chunk index) with vectors

## Logging — structlog

- Use **structlog** for all logging
- Bind trace IDs at request entry and propagate through the call chain
- Log levels: `debug` for internal flow, `info` for operations, `warning` for recoverable issues, `error` for failures
- Never log secrets, tokens, or full request bodies in production

## Linting & Formatting

- **ruff** is the single linter and formatter
- Lint: `ruff check .`
- Format: `ruff format .`
- Fix auto-fixable issues: `ruff check . --fix`
- All code must pass `ruff check` with zero errors before merge

## Testing

- **pytest** with **pytest-asyncio** for async test support
- Run all tests: `pytest`
- Stop on first failure: `pytest -x`
- Test files live alongside source or in a `tests/` directory mirroring `src/`
- Use `httpx.AsyncClient` with FastAPI's `TestClient` (via `ASGITransport`) for integration tests
- Mock external services (Qdrant, node agents, LLMs) in unit tests

## Package Management

- **uv** preferred, **pip** as fallback
- Dependencies declared in `pyproject.toml`
- Lock file committed to repo

## MCP Tool Handler Rules

- All MCP tool handlers **validate inputs against registries** before executing
- Unknown repo names, node IDs, or write targets → reject with a clear error, never guess
- All tool calls **logged with trace IDs** via structlog
- **Fail closed** on unknown targets — if a target cannot be resolved, return an error rather than attempting a fallback

## Import Conventions

- Standard library → third-party → local, separated by blank lines
- Use absolute imports from package root (`from src.hub.registry import node_registry`)
- No wildcard imports (`from x import *`)
