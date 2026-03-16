# Agent Catalog

Prefix: `gpttalker`

Visible entrypoint:

- `gpttalker-team-leader`

Core hidden specialists:

- `gpttalker-planner`
- `gpttalker-plan-review`
- `gpttalker-implementer`
- `gpttalker-reviewer-code`
- `gpttalker-reviewer-security`
- `gpttalker-tester-qa`
- `gpttalker-docs-handoff`

Utility hidden specialists:

- `gpttalker-utility-explore`
- `gpttalker-utility-shell-inspect`
- `gpttalker-utility-summarize`
- `gpttalker-utility-ticket-audit`
- `gpttalker-utility-github-research`
- `gpttalker-utility-web-research`

Workflow contract:

- the team leader advances stages through ticket tools and workflow state, not by manually editing ticket files
- each major stage must leave a canonical artifact before the next stage begins
- read-only specialists return findings, artifacts, or blockers instead of mutating repo files
