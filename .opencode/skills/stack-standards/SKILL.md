---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack:

- Python 3.11+
- FastAPI
- Pydantic v2
- aiosqlite for structured runtime state
- Qdrant for semantic context
- httpx async clients for outbound HTTP
- Tailscale as the internal transport boundary

Implementation rules:

- use type hints on functions, return values, and non-obvious locals
- prefer `str | None` over `Optional[str]`
- use Pydantic models for API request and response schemas
- make FastAPI endpoints `async def`
- use `fastapi.Depends` for dependency injection
- never use synchronous sqlite APIs in async request paths
- use `httpx.AsyncClient` with explicit timeouts on outbound calls
- use structured logging; do not add bare `print()` calls
- log tool execution with `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, and `duration_ms`
- redact secrets, tokens, passwords, and raw file contents from logs
- fail closed on unknown nodes, repos, write targets, and service aliases

Validation commands:

- bootstrap the repo-local environment with `uv sync --locked --extra dev`
- run tests with `.venv/bin/python -m pytest`
- run lint with `.venv/bin/ruff check .`
- use `.venv/bin/python --version` and `.venv/bin/pytest --version` when bootstrap or QA needs executable proof

Repo-specific focus areas:

- hub code lives under `src/hub/`
- node-agent code lives under `src/node_agent/`
- shared models, config, and logging code live under `src/shared/`
- MCP tool handlers need at least one happy-path and one error-path test
- repo-inspection and write-target logic must keep normalized-path and fail-closed behavior intact
