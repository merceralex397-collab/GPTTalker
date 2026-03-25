---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack:

- Python 3.11+
- FastAPI for the hub and node-agent HTTP surfaces
- SQLite via `aiosqlite` for structured runtime state
- Qdrant for semantic project context
- `httpx` for outbound hub and node-agent HTTP
- `uv` for environment and dependency management

Core coding rules:

- use type hints on function signatures, return values, and non-obvious variables
- prefer `str | None` over `Optional[str]`
- use Pydantic models for API request and response schemas
- keep FastAPI endpoints `async`
- use `fastapi.Depends` for dependency injection
- never call synchronous sqlite APIs from async code paths
- use explicit timeouts on every `httpx` call
- treat Tailscale as the internal transport boundary
- use structured logging, never bare `print()`
- redact secrets, tokens, passwords, and raw file contents from logs
- fail closed on unknown nodes, repos, write targets, and service aliases

Repo-sensitive areas:

- workflow and ticketing surfaces under `.opencode/`, `docs/process/`, `START-HERE.md`, and `tickets/`
- hub policy and path-validation code under `src/hub/policy/`
- repo inspection and markdown-delivery tools under `src/hub/tools/`
- node-agent bounded execution under `src/node_agent/`
- shared logging, schemas, and repository helpers under `src/shared/`

Validation commands:

- install or refresh the environment with `UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev`
- run the full suite with `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short`
- run focused pytest targets when a ticket scopes them explicitly
- lint with `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- format with `UV_CACHE_DIR=/tmp/uv-cache uv run ruff format .`

Testing rules:

- every MCP tool handler must keep at least one happy-path and one error-path test
- QA and implementation artifacts must include raw command output, not code-inspection-only claims
- if git-based tests or temporary repos require identity, configure git first rather than treating the failure as a product defect
- if a command cannot run because `uv`, `pytest`, `rg`, git identity, or another executable is missing, return a blocker instead of inventing workflow workarounds

Execution guidance:

- do not widen path or write-target trust boundaries to satisfy tests
- preserve repo-specific model pinning to `MiniMax-M2.7` unless the human explicitly changes it
- keep workflow repairs separate from source-layer bug fixes; route product defects into tickets rather than hiding them inside managed-surface edits
