---
name: review-audit-bridge
description: Keep code review, security review, and QA passes evidence-based and stage-aware for this repo. Use when a ticket already has an approved plan and implementation evidence and a review lane needs structured findings.
---

# Review Audit Bridge

Before starting a code review, security review, or QA pass, call `skill_ping` with `skill_id: "review-audit-bridge"` and `scope: "project"`.

Use this skill after implementation exists. It bridges the review and QA lanes so they return evidence-backed findings instead of vague commentary.
This is a generated repo-local skill. It may recommend remediation or reverification follow-up, but it does not become the canonical ticket owner by itself.

Repo-specific validation priorities:

- hub contract and security tickets: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/ -q --tb=no`
- node-agent executor tickets: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/node_agent/test_executor.py -q --tb=no`
- shared-runtime logging tickets: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/shared/test_logging.py -q --tb=no`
- broad regression check: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ --collect-only -q --tb=no` followed by `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/ -v`
- lint baseline: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`

Security-sensitive areas that need explicit attention:

- `src/hub/policy/` for path normalization, write-target scoping, and fail-closed checks
- `src/hub/tools/` and `src/hub/tool_routing/` for MCP handler contracts
- `src/node_agent/executor.py` for allowed-path enforcement and filesystem metadata
- `src/shared/logging.py` and `src/shared/context.py` for redaction and trace propagation

Prioritize findings in this order:

1. correctness bugs
2. behavior regressions
3. security or trust issues
4. missing tests or validation gaps
5. maintainability concerns

Return:

- For code review or security review:
  1. Findings ordered by severity
  2. Risks
  3. Validation gaps
  4. Blockers or approval signal
- For QA:
  1. Checks run
  2. Pass or fail
  3. Blockers
  4. Closeout readiness

Rules:

- findings come first; do not open with praise or a summary
- reference exact files, diffs, commands, or artifact paths
- if the approved plan, implementation artifact, or required validation context is missing, return a blocker instead of inferring correctness
- use `ticket-execution` for lifecycle order and `project-context` for canonical repo docs
- write any workflow-failure explanation or review retrospective under `diagnosis/<timestamp>/` or the repo-local process-log path described in `references/review-contract.md`
- recommend follow-up tickets only when current evidence justifies them, and route canonical ticket creation through the repo's guarded ticket workflow
- do not claim that repo files changed

## References

- `references/review-contract.md`
