---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

GPTTalker stack: `Python 3.11+`, `FastAPI`, `Pydantic v2`, `aiosqlite`, `httpx`, `Qdrant`, `uv`, `pytest`, `ruff`.

## Runtime And Structure

- The hub entrypoint is `src/hub/main.py`; the node-agent entrypoint is `src/node_agent/main.py`.
- Shared runtime contracts, schemas, repositories, and logging live under `src/shared/`.
- Treat Tailscale as the only internal transport boundary and ngrok as the only canonical public-edge provider after the 2026-03-31 pivot.
- SQLite owns structured runtime records; Qdrant owns semantic project context. Do not replace either with ad hoc local files.

## Python And FastAPI Rules

- Use Python 3.11 syntax and explicit type hints throughout implementation and tests.
- Keep FastAPI endpoints `async` and keep outbound network calls on `httpx` async clients with explicit timeouts.
- Use Pydantic models for request and response schemas instead of ad hoc dictionaries.
- Fail closed on unknown nodes, repos, write targets, and LLM aliases. Policy checks belong at the boundary before execution.
- Do not log secrets, raw tokens, or unbounded file contents.

## Dependency Injection And Import Safety

- Prefer `fastapi.Depends` for dependency wiring and keep dependency providers in the relevant `dependencies.py` module.
- When a dependency function only imports a type under `TYPE_CHECKING`, use a string annotation such as `-> "SessionStore"` so runtime imports still succeed.
- In FastAPI dependency functions, type the injected request object as `Request`, not `FastAPI`.
- Before closeout on hub or node-agent tickets, prove imports still resolve with:
  - `PYTHONPATH=src python3 -c 'from src.hub.main import app'`
  - `PYTHONPATH=src python3 -c 'from src.node_agent.main import app'`
- Treat import failures as blocking evidence. Do not replace them with narrative PASS claims.

## Validation Commands

Use the repo-owned commands first:

- Bootstrap dependencies: `UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev`
- Lint: `python3 -m scripts.run_lint`
- Tests: `python3 -m scripts.run_tests --tb=short`
- Full validation: `python3 -m scripts.validate`

Equivalent make targets exist and are acceptable when the environment is already prepared:

- `make lint`
- `make test`
- `make validate`

For review, QA, and remediation closeout, prefer the smallest command set that proves the changed surface is still valid:

- Import checks:
  - `PYTHONPATH=src python3 -c 'from src.hub.main import app'`
  - `PYTHONPATH=src python3 -c 'from src.node_agent.main import app'`
- Ruff gates:
  - `python3 -m ruff check src/ tests/ scripts/`
  - `python3 -m ruff format --check src/ tests/ scripts/`
- Pytest:
  - `PYTHONPATH=src TEST_DB_URL=sqlite+aiosqlite:///:memory: LOG_LEVEL=WARNING python3 -m pytest tests/ -v --tb=short`

If a remediation ticket carries `finding_source`, rerun the original finding-producing command first and include the raw output in the review or QA artifact before claiming the issue is fixed.

## Testing Expectations

- Every MCP tool or policy branch needs at least one happy-path and one failure-path test.
- Add hub tests under `tests/hub/`, node-agent tests under `tests/node_agent/`, and shared-library tests under `tests/shared/`.
- Use `TEST_DB_URL=sqlite+aiosqlite:///:memory:` for test runs unless the ticket explicitly requires a different database surface.
- Keep smoke scope aligned to the active ticket. Do not broaden process-remediation smoke into full product boot checks when prerequisite feature tickets remain open.

## Process Rules

- Use ticket tools and registered artifacts for stage movement; do not advance lifecycle state by raw file edits.
- `smoke_test` is the only legal producer of smoke-test artifacts.
- Review and QA artifacts must include the exact commands run and the raw output, especially for remediation tickets that exist to clear prior findings.
- `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived surfaces. Durable truth remains in `docs/spec/CANONICAL-BRIEF.md`, `tickets/manifest.json`, and `.opencode/state/workflow-state.json`.
