---
name: repo-navigation
description: Navigate the canonical docs, ticket files, and OpenCode operating surfaces for this repo. Use when an agent needs to find where process, state, or handoff information lives without scanning the entire repository.
---

# Repo Navigation

Before navigating, call `skill_ping` with `skill_id: "repo-navigation"` and `scope: "project"`.

Canonical paths:

- `README.md` - operator-facing project summary and bootstrap commands
- `AGENTS.md` - repo rules, truth hierarchy, required read order, and team contract
- `docs/spec/CANONICAL-BRIEF.md` - durable product facts and accepted decisions
- `docs/process/` - workflow contract, agent catalog, tooling, model matrix, git capability
- `tickets/` - manifest-backed queue, derived board, and per-ticket markdown files
- `.opencode/agents/` - repo-local agent prompts
- `.opencode/skills/` - repo-local procedures and model guidance
- `.opencode/tools/` - workflow, artifact, bootstrap, handoff, and smoke-test tools
- `.opencode/state/` - canonical artifact bodies, workflow-state, and derived restart surfaces
- `.opencode/meta/` - bootstrap provenance and repair execution history

Code ownership map:

- `src/hub/` - FastAPI hub app, MCP tool handlers, policy engine, transport, services
- `src/node_agent/` - per-node executor and HTTP surface
- `src/shared/` - schemas, repositories, config, exceptions, structured logging
- `tests/hub/` - tool-contract and security coverage
- `tests/node_agent/` - executor/path behavior coverage
- `tests/shared/` - logging and shared-runtime coverage

When triaging current failures, start here:

- hub path and write-target issues: `src/hub/policy/`, `src/hub/tools/`, `tests/hub/test_security.py`, `tests/hub/test_contracts.py`
- node-agent executor issues: `src/node_agent/executor.py`, `tests/node_agent/test_executor.py`
- shared logging issues: `src/shared/logging.py`, `tests/shared/test_logging.py`
