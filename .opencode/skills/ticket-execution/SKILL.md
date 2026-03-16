---
name: ticket-execution
description: Follow GPTTalker's ticket lifecycle with domain-specific validation gates. Use when an agent is advancing a ticket through planning, review, implementation, QA, and closeout.
---

# Ticket Execution — GPTTalker

## Required Lifecycle Order

1. **Ticket lookup** — read the ticket file and understand scope
2. **Planning** — design the approach, identify affected modules
3. **Plan review** — validate the plan covers edge cases and security
4. **Implementation** — write the code
5. **Code review** — review for correctness and standards compliance
6. **Security review** — required for any change touching registries, routing, auth, or file writes
7. **QA** — run tests and validate behavior
8. **Handoff and closeout** — update ticket status, refresh handoff artifacts

## GPTTalker-Specific Implementation Rules

### Specialized Implementers

GPTTalker uses three specialized implementation domains. Route ticket work to the correct one:

| Domain | Scope | Key Paths |
|---|---|---|
| **Hub** | MCP tool handlers, registries, routing, policy engine | `src/hub/` |
| **Node-agent** | Local operations, repo inspection, file delivery, local LLM | `src/node_agent/` |
| **Context** | Qdrant integration, indexing pipeline, context bundles, search | `src/hub/context/` |

### Validation Gates Before Review

Every implementation must pass these checks before entering code review:

1. **`pytest`** — all tests pass (zero failures)
2. **`ruff check .`** — zero linting errors
3. **MCP contract compliance** — if the ticket touches an MCP tool, verify the tool's request/response schema matches the contract defined in `docs/spec/CANONICAL-BRIEF.md`

### Additional Rules

- Changes to shared models (`src/shared/`) require testing from both hub and node-agent perspectives
- Registry changes must include tests for the reject-unknown-target behavior
- Any new MCP tool must be added to the tool registration surface and documented in the canonical brief
