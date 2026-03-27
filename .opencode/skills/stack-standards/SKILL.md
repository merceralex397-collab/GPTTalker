---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack: Python 3.11+ with FastAPI, `uv`, `pytest`, `ruff`, SQLite via `aiosqlite`, Qdrant, and async HTTP using `httpx`.

Language and framework rules:

- use Python 3.11+ syntax and complete type hints on public functions, async helpers, and non-obvious locals
- keep FastAPI endpoints async and prefer `fastapi.Depends` for dependency injection
- use Pydantic models for API request and response contracts
- prefer `str | None` over `Optional[str]`
- do not use synchronous sqlite access on async paths; runtime persistence stays on `aiosqlite`
- use async `httpx` clients with explicit timeouts for outbound hub or node-agent traffic
- treat Tailscale as the internal transport boundary; unknown nodes, repos, write targets, and service aliases fail closed

Security and logging rules:

- normalize and validate user-supplied paths before filesystem access
- preserve atomic writes for markdown delivery and other scoped file outputs
- keep structured logs free of raw secrets, tokens, passwords, and large file bodies
- use structured logging helpers instead of `print()`
- preserve fail-closed behavior for write-target lookup, repo lookup, and service routing

Validation rules:

- bootstrap dependencies with `UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev`
- run `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ --collect-only -q --tb=no` before broad Python validation when touching imports, routing, or shared runtime code
- targeted ticket validation should use the acceptance command recorded on the ticket whenever one exists
- full-suite validation is `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v`
- lint with `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`

Repo-specific reminders:

- hub work usually lives under `src/hub/` and must preserve MCP transport and policy contracts covered by `tests/hub/`
- node-agent work usually lives under `src/node_agent/` and must keep allowed-path enforcement strict
- shared-runtime work usually lives under `src/shared/` and must preserve nested redaction semantics and trace propagation
- when a ticket changes runtime entrypoints or dependency wiring, include an import check for the affected module in implementation and QA proof
