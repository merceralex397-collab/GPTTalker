# SETUP-001: Project skeleton and dependencies

## Summary

Bootstrap the GPTTalker repository with a proper Python project structure using pyproject.toml for dependency management. Create the core package directories (src/hub/, src/node_agent/, src/shared/) with __init__.py files, establishing the monorepo layout that separates hub server, node agent, and shared utilities. Pin all key dependencies: FastAPI, uvicorn, aiosqlite, httpx, qdrant-client, pydantic, structlog, ruff, and pytest.

## Stage

planning

## Status

todo

## Depends On

- None

## Acceptance Criteria

- [ ] pyproject.toml exists with all required dependencies and correct Python version constraint (>=3.11)
- [ ] src/hub/__init__.py exists
- [ ] src/node_agent/__init__.py exists
- [ ] src/shared/__init__.py exists
- [ ] `pip install -e .` succeeds in a clean venv
- [ ] ruff and pytest are available as dev dependencies
- [ ] .gitignore covers Python, venv, __pycache__, .env

## Artifacts

- None yet

## Notes

- Use src layout (not flat) to keep hub and node_agent as separate importable packages
- Consider adding optional dependency groups: [dev] for ruff/pytest, [node] for node-agent-only deps
- structlog chosen over stdlib logging for structured JSON output
