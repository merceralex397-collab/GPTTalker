---
name: stack-standards
description: Hold the project-local standards for GPTTalker's Python, FastAPI, storage, networking, validation, and runtime assumptions. Use when planning or implementing work that must follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack:

- Python 3.11+ application code
- FastAPI hub and node-agent services
- SQLite via `aiosqlite` for structured runtime state
- Qdrant for semantic project context
- `httpx` async clients for outbound service calls
- Tailscale as the internal transport boundary
- `ruff` for linting and formatting
- `pytest` plus `pytest-asyncio` for validation

Core implementation rules:

- use type hints on function signatures, return values, and non-obvious variables
- prefer `str | None` over `Optional[str]`
- use Pydantic models for API request and response schemas
- keep FastAPI endpoints async and use `fastapi.Depends` for dependency injection
- do not use synchronous sqlite APIs in async paths
- treat unknown nodes, repos, write targets, and service aliases as fail-closed errors
- use structured logging; do not add bare `print()` calls
- redact secrets, tokens, passwords, and raw file contents from logs
- log tool activity with `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, and `duration_ms`
- preserve the Tailscale-only trust boundary for internal hub-to-node traffic

Validation rules:

- prefer `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` for repo-wide lint validation
- use `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ --collect-only -q --tb=no` before broader Python test runs when import or collection risk is relevant
- use `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=no` for the project test suite unless the ticket defines a narrower canonical command
- when a ticket acceptance criterion defines an explicit smoke command, treat that command as canonical over heuristic test selection
- if `uv`, `pytest`, `ruff`, or another required executable is missing, return a blocker instead of improvising a workaround

Safety notes:

- keep changes mechanical when addressing lint-only tickets unless the approved plan explicitly allows broader behavior changes
- preserve FastAPI dependency patterns that intentionally rely on `Depends(...)`; do not "fix" them into non-idiomatic alternatives
- prefer repo-local environment/bootstrap flows over ad hoc package-manager commands when bootstrap state is missing, stale, or failed
