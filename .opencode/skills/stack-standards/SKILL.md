---
name: stack-standards
description: Hold GPTTalker’s project-local standards for Python, FastAPI, SQLite, Qdrant, validation, and runtime safety.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current scaffold mode: `Python + FastAPI`

## Engineering rules

- Python 3.11+ with explicit type hints
- FastAPI async handlers only
- Pydantic models for API boundaries
- `aiosqlite` for async structured storage
- `httpx.AsyncClient` with explicit timeouts for outbound HTTP
- Qdrant for semantic project context
- structured logging with redaction
- fail closed on unknown nodes, repos, write targets, or model aliases

## Validation commands

- `ruff check .`
- `ruff format --check .`
- `pytest`
- additional ticket-specific validation may include `uv run pytest` or focused test modules
