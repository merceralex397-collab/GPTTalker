---
name: review-audit-bridge
description: Run GPTTalker code review, security review, and QA passes with repo-specific commands, artifact paths, and blocker rules.
---

# Review Audit Bridge

Use this after approved planning and implementation evidence already exist.

## Required Inputs

- The ticket entry in `tickets/manifest.json`
- The current workflow state in `.opencode/state/workflow-state.json`
- The stage artifacts under `.opencode/state/` or `.opencode/state/artifacts/history/`

If the approved plan, implementation artifact, or required validation context is missing, return a blocker.

## Review Output Shape

- Findings ordered by severity
- Risks or regression notes
- Validation gaps
- Approval signal or blocker

## QA Output Shape

- Commands run
- Result per check
- Blockers
- Closeout readiness

## Repo-Specific Commands

- Bootstrap: `UV_CACHE_DIR=/tmp/uv-cache uv sync --locked --extra dev`
- Lint: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- Full tests: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -q --tb=short`
- Import smoke:
  - `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.hub.main import app"`
  - `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "from src.node_agent.main import app"`

## High-Risk Areas

- `src/hub/policy/` path, repo, and write-target enforcement
- `src/hub/tools/markdown.py` and node-agent write execution
- FastAPI dependency wiring in `src/hub/` and `src/node_agent/`
- `src/shared/logging.py` redaction and trace propagation
- ngrok edge startup/config paths in `src/hub/config.py`, `src/hub/lifespan.py`, and `src/hub/services/tunnel_manager.py`

## Approval Rules

- Code review blocks on correctness regressions, broken contracts, or missing proof.
- Security review blocks on trust-boundary drift, path escape, auth regression, or secret leakage.
- QA blocks when required commands cannot run and no explicit environment blocker is recorded.
- Recommend remediation or reverification tickets only when current evidence supports them. Do not become the canonical ticket owner.

## Process Logging

- Put workflow-misuse explanations or repo-local review retrospectives under `diagnosis/` when the issue is process evidence rather than product code.

## References

- `references/review-contract.md`
