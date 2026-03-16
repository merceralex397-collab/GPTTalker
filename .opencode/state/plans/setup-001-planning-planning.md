# SETUP-001 Implementation Plan: Project Skeleton and Dependency Baseline

## 1. Scope

Create the foundational Python project structure, dependency management, and validation tooling that enables subsequent tickets to implement domain-specific functionality. This ticket establishes the mechanical infrastructure only—hub logic, node-agent implementation, and shared runtime behavior are handled in later tickets.

## 2. Files and Systems Affected

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `pyproject.toml` | Project metadata, dependency declarations, build configuration |
| `src/__init__.py` | Package marker for src/ |
| `src/hub/__init__.py` | Hub package marker |
| `src/hub/main.py` | FastAPI application entrypoint (stub) |
| `src/hub/config.py` | Configuration loading stub |
| `src/hub/routes.py` | Route placeholder |
| `src/hub/mcp.py` | MCP protocol handling stub |
| `src/node_agent/__init__.py` | Node agent package marker |
| `src/node_agent/main.py` | Node agent service entrypoint (stub) |
| `src/node_agent/config.py` | Configuration loading stub |
| `src/node_agent/executor.py` | Operation executor stub |
| `src/shared/__init__.py` | Shared package marker |
| `src/shared/models.py` | Pydantic model placeholders |
| `src/shared/config.py` | Shared configuration patterns |
| `src/shared/logging.py` | Structured logging setup |
| `src/shared/exceptions.py` | Shared exception classes |
| `pytest.ini` | Pytest configuration |
| `tests/__init__.py` | Test package marker |
| `tests/conftest.py` | Pytest fixtures |
| `ruff.toml` | Ruff linter configuration |
| `.gitignore` | Git ignore patterns for Python |
| `scripts/setup.sh` | Development environment bootstrap (optional) |

### Systems Modified

- Project metadata system (pyproject.toml)
- Python import system (__init__.py files)
- Validation tooling (pytest, ruff configs)
- Git configuration (.gitignore)

## 3. Implementation Steps

### Step 1: Create pyproject.toml with Dependencies

Define the project metadata and declare all runtime, development, and optional dependencies.

**Key sections:**
- `[project]` — name, version, description, Python 3.11+ requirement
- `[project.dependencies]` — fastapi, uvicorn, aiosqlite, httpx, pydantic, qdrant-client
- `[project.optional-dependencies]` — dev (pytest, pytest-asyncio, ruff)
- `[build-system]` — setuptools + pyproject.toml backend
- `[tool.pytest.ini_options]` — asyncio mode, test paths
- `[tool.ruff]` — linting rules, line length, target Python 3.11

### Step 2: Establish src/ Directory Structure

Create the three primary packages with minimal stub modules:

```
src/
├── __init__.py
├── hub/
│   ├── __init__.py
│   ├── main.py       # app = FastAPI() definition
│   ├── config.py     # Config loading from env
│   ├── routes.py     # @router.get("/health") stub
│   └── mcp.py        # MCP protocol handler stub
├── node_agent/
│   ├── __init__.py
│   ├── main.py       # async def main() entrypoint
│   ├── config.py     # Agent configuration
│   └── executor.py   # Bounded operation executor stub
└── shared/
    ├── __init__.py
    ├── models.py     # Base Pydantic models (empty placeholders)
    ├── config.py     # Shared config patterns
    ├── logging.py    # structured_logger setup
    └── exceptions.py # GPTTalkerError, ValidationError stubs
```

**Each stub module should:**
- Import any required types (e.g., FastAPI, AsyncSession)
- Define minimal class/function signatures with `pass` or `...` bodies
- Include docstrings explaining future purpose

### Step 3: Configure pytest

Create `pytest.ini` with:
- `asyncio_mode = auto` — automatic async test handling
- `testpaths = tests` — explicit test directory
- `filterwarnings = ignore` — optional warning suppression for dependencies
- `conftest.py` in tests/ with:
  - `@pytest.fixture` for async client (future use)
  - `@pytest.fixture` for mock config

### Step 4: Configure ruff

Create `ruff.toml` with:
- `target-version = "py311"` — Python 3.11+
- `line-length = 100` — per AGENTS.md conventions
- `select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]` — sensible rule set
- `ignore = ["E501"]` — let line-length handle formatting
- `[isort]` — import sorting configuration
- `[per-file-ignores]` — __init__.py exceptions

### Step 5: Create .gitignore

Add standard Python ignores:
- `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.ruff_cache/`
- `*.egg-info/`, `dist/`, `build/`
- `.env`, `.env.local`
- `*.db` (SQLite files, except migrations if any)
- `.DS_Store`

### Step 6: Verify Dependency Resolution

Run `uv sync` or `pip install -e ".[dev]"` to confirm:
- All declared dependencies resolve without conflict
- Python 3.11+ is detected
- ruff and pytest are available in PATH

### Step 7: Validate Import Structure

Confirm:
- `python -c "from src.hub.main import app; print(app)"` runs without import errors
- `python -c "from src.node_agent.main import main; print(main)"` runs without import errors
- `python -c "from src.shared.models import *"` runs without import errors
- `ruff check src/` runs and reports only expected results
- `pytest --collect-only` discovers tests (even if empty)

## 4. Validation Plan

| Check | Command | Expected Outcome |
|-------|---------|------------------|
| Dependency resolution | `uv sync` or `pip install -e ".[dev]"` | Exit code 0, no conflicts |
| Hub import | `python -c "from src.hub.main import app; print(app)"` | FastAPI instance printed |
| Node agent import | `python -c "from src.node_agent.main import main; print(main)"` | Function printed |
| Shared import | `python -c "from src.shared import models, logging, exceptions; print('ok')"` | "ok" printed |
| Ruff linting | `ruff check src/` | Zero errors (warnings acceptable) |
| Pytest collection | `pytest --collect-only` | Test collection succeeds |
| Python version | `python --version` | 3.11.x or higher |

## 5. Risks and Assumptions

### Risks
- **Dependency conflicts**: Some combinations of httpx, qdrant-client, and FastAPI versions may conflict. Mitigation: pin compatible versions in pyproject.toml.
- **Import cycle**: Placing too much in `src/shared` before architecture is known could create cycles. Mitigation: keep shared module placeholders minimal and decoupled.

### Assumptions
- Python 3.11+ is available on the operator's machine
- `uv` is the preferred package manager (or pip fallback is acceptable)
- The directory structure matches the canonical brief's `src/hub`, `src/node_agent`, `src/shared` split
- Later tickets will populate stub modules with real implementation

## 6. Blockers and Required User Decisions

### Blockers
None. This ticket has no dependencies and all blocking decisions from the canonical brief are resolved.

### Required Decisions
| Decision | Options | Recommended | Rationale |
|----------|---------|-------------|-----------|
| Package manager | `uv` / `pip` | `uv` | Faster, lockfile support, matches canonical brief |
| FastAPI version | latest stable | latest stable | Avoid pinning unless conflicts emerge |
| Qdrant client version | latest stable | latest stable | Deferred to CTX-001 ticket |
| Python environment | venv / uv venv / conda | `uv venv` | Lightweight, matches uv preference |

## 7. Post-Implementation State

After this ticket:
- `src/` contains three packages with placeholder modules
- `pyproject.toml` declares all known dependencies
- `pytest.ini` and `ruff.toml` configure validation tooling
- `.gitignore` excludes build artifacts
- The repo is ready for SETUP-002 (shared schemas, config loading, logging)
- Domain-specific hub, node-agent, or shared code can be implemented in subsequent tickets

## 8. Artifact Summary

| Artifact | Path | Kind |
|----------|------|------|
| Planning artifact | `.opencode/state/plans/setup-001-planning-plan.md` | planning |
| (Implementation artifact will be created in implementation stage) | | |
