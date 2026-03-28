---
name: stack-standards
description: Apply GPTTalker's repo-local Python, FastAPI, storage, networking, logging, and validation conventions. Use when planning, implementing, or reviewing code that must match this repo's actual engineering contract.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

## Stack Summary

- Language: Python 3.11+
- API layer: FastAPI
- Structured storage: SQLite through `aiosqlite`
- Semantic context storage: Qdrant via `qdrant-client`
- Outbound HTTP: async `httpx` with explicit timeouts
- Validation: `pytest`, `pytest-asyncio`, `ruff`

## Python Rules

- Use type hints on public functions, return values, and non-obvious locals.
- Prefer modern union syntax such as `str | None`.
- Keep async paths fully async; do not call synchronous sqlite APIs from FastAPI handlers or other async services.
- Use small, explicit helpers over hidden side effects.

## FastAPI Rules

- Endpoints must be `async def`.
- Use Pydantic models for request and response contracts.
- Use `fastapi.Depends` for dependency injection rather than ad hoc request wiring.
- Follow the repo's dependency modules and service wrappers instead of creating duplicate app-state access patterns.
- FastAPI `Depends(...)` in function defaults is expected in this repo; `ruff` B008 is intentionally ignored for those paths.

## Storage And Context Rules

- SQLite runtime state belongs in async `aiosqlite` repositories and helpers under `src/shared/` and hub/node-agent services.
- Qdrant is the semantic memory layer for indexed repo content, issues, context bundles, and cross-repo intelligence.
- Preserve idempotent indexing and content-hash tracking behavior when changing context flows.

## Networking And Security Rules

- Use async `httpx` for hub-to-node and hub-to-service calls.
- Set an explicit timeout on every outbound `httpx` request.
- Treat Tailscale as the internal transport boundary; do not introduce broader trust assumptions.
- Fail closed on unknown nodes, repos, write targets, and service aliases.
- Normalize user-influenced paths and reject traversal or escaping behavior.

## Logging And Audit Rules

- Use structured logging helpers from `src/shared/logging.py`; do not add bare `print()` calls.
- Keep log payloads redacted for secrets, tokens, passwords, and raw file contents.
- Preserve audit-oriented metadata on tool flows, including trace IDs and outcome data, when changing hub or node-agent execution paths.

## Validation Commands

- Lint: `ruff check .`
- Tests: `pytest`
- Targeted repo scripts are also available:
  - `gpttalker-lint`
  - `gpttalker-test`
  - `gpttalker-validate`

## Testing Expectations

- Add or update `pytest` coverage for behavior changes.
- MCP tool handlers need at least one happy-path and one error-path test.
- Use `pytest-asyncio` patterns for async behavior and FastAPI-adjacent async services.
- Treat blocked validation as a real blocker; do not claim PASS without executable evidence.

## Review Focus

- Check FastAPI dependency wiring, async boundaries, path validation, and logging redaction first.
- Check persistence changes for missing commits, transaction drift, or sync/async mixing.
- Check context and cross-repo flows for Qdrant schema drift, indexing regressions, and policy bypasses.
