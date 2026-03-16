# SETUP-005: Test infrastructure

## Summary

Set up the testing infrastructure for GPTTalker with pytest, async test support, and standard fixtures. Configure ruff for linting and formatting. Provide reusable test fixtures for in-memory SQLite databases and FastAPI test clients so that all subsequent feature tickets can write tests efficiently.

## Stage

planning

## Status

todo

## Depends On

- SETUP-001

## Acceptance Criteria

- [ ] pytest.ini or pyproject.toml [tool.pytest] section configured
- [ ] pytest-asyncio installed and configured for async test support
- [ ] Fixture: in-memory SQLite database with schema applied
- [ ] Fixture: FastAPI TestClient with app and database wired
- [ ] Fixture: sample node, repo, and write-target data
- [ ] ruff.toml or pyproject.toml [tool.ruff] section configured with sensible rules
- [ ] `pytest` runs successfully with zero tests (no collection errors)
- [ ] `ruff check src/` runs clean on skeleton code
- [ ] CI-friendly: tests can run without external services

## Artifacts

- None yet

## Notes

- Use anyio backend for pytest-asyncio to match FastAPI's async model
- httpx.AsyncClient preferred over Starlette TestClient for async test support
- Consider conftest.py hierarchy: root, hub, node_agent
