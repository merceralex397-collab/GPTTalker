# Initial Codebase Review

## Scope

- subject repo: /home/pc/projects/GPTTalker
- diagnosis timestamp: 2026-04-09T11:54:02Z
- audit scope: managed workflow, restart, ticket, prompt, and execution surfaces
- verification scope: current repo state only

## Result State

- result_state: validated failures found
- finding_count: 11
- errors: 8
- warnings: 3

## Validated Findings

### Workflow Findings

### CONFIG001

- finding_id: CONFIG001
- summary: opencode.jsonc is missing the 'model' field.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: opencode.jsonc
- observed_or_reproduced: The template used to scaffold this repo did not include a model assignment, or repair has not yet propagated the updated template.
- evidence:
  - Current config keys: ['$schema', 'instructions', 'mcp', 'permission']
- remaining_verification_gap: None recorded beyond the validated finding scope.

### CONFIG002

- finding_id: CONFIG002
- summary: opencode.jsonc is missing the 'default_agent' field.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: opencode.jsonc
- observed_or_reproduced: The template used to scaffold this repo did not include a default_agent assignment. Without this, opencode falls back to the built-in 'build' agent instead of the project's team-leader.
- evidence:
  - Current config keys: ['$schema', 'instructions', 'mcp', 'permission']
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW010

- finding_id: WFLOW010
- summary: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: tickets/manifest.json, .opencode/state/workflow-state.json, .opencode/meta/pivot-state.json, START-HERE.md, .opencode/state/context-snapshot.md, .opencode/state/latest-handoff.md
- observed_or_reproduced: `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are not being regenerated from `tickets/manifest.json`, `.opencode/state/workflow-state.json`, and `.opencode/meta/pivot-state.json` after workflow mutations or managed repair, leaving bootstrap, repair-follow-on, pivot, verification, lane-lease, or active-ticket state stale.
- evidence:
  - START-HERE.md handoff_status drift: expected 'pivot follow-up required' from canonical state, found 'ready for continued development'.
  - START-HERE.md pivot_in_progress drift: expected 'true' from canonical state, found 'false'.
  - .opencode/state/context-snapshot.md pivot_in_progress drift: expected 'true' from canonical state, found 'false'.
  - .opencode/state/latest-handoff.md handoff_status drift: expected 'pivot follow-up required' from canonical state, found 'ready for continued development'.
  - .opencode/state/latest-handoff.md pivot_in_progress drift: expected 'true' from canonical state, found 'false'.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW012

- finding_id: WFLOW012
- summary: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: docs/process/workflow.md, tickets/README.md, .opencode/commands/kickoff.md, .opencode/commands/run-lane.md, .opencode/skills/ticket-execution/SKILL.md, .opencode/agents/gpttalker-team-leader.md, .opencode/agents/gpttalker-implementer-context.md, .opencode/agents/gpttalker-lane-executor.md, .opencode/agents/gpttalker-docs-handoff.md
- observed_or_reproduced: Some workflow docs and prompts still describe worker-owned lease claims while others expect the team leader to coordinate claims. That contradiction is enough to make weaker models thrash around ticket ownership and pre-bootstrap write rules.
- evidence:
  - .opencode/skills/ticket-execution/SKILL.md does not state that the team leader owns ticket_claim and ticket_release.
  - .opencode/skills/ticket-execution/SKILL.md does not limit pre-bootstrap write claims to Wave 0 setup work.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW016

- finding_id: WFLOW016
- summary: The managed smoke-test override contract can fail before the requested smoke command even starts.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/tools/smoke_test.ts
- observed_or_reproduced: The generated `smoke_test` tool passes `command_override` directly into `spawn()` argv and does not separate shell-style environment assignments like `UV_CACHE_DIR=...` from the executable. Valid repo-standard override commands can therefore misfire as `ENOENT` instead of running the intended smoke check.
- evidence:
  - .opencode/tools/smoke_test.ts does not classify quote or shell-shape failures as syntax_error instead of generic command failure.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW023

- finding_id: WFLOW023
- summary: The generated lifecycle contract is not verdict-aware, so FAIL review or QA artifacts can still look advanceable.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/tools/ticket_lookup.ts, .opencode/tools/ticket_update.ts, .opencode/lib/workflow.ts
- observed_or_reproduced: Transition guidance and transition enforcement must inspect artifact verdicts, not just artifact existence. Otherwise weaker models continue on the happy path after blocker findings.
- evidence:
  - .opencode/tools/ticket_lookup.ts does not make review FAIL verdicts route back to implementation.
  - .opencode/tools/ticket_lookup.ts does not make QA FAIL verdicts route back to implementation.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW024

- finding_id: WFLOW024
- summary: Fail-state routing is still under-specified in generated prompts or workflow skills.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/skills/ticket-execution/SKILL.md
- observed_or_reproduced: Even if the tool contract knows how to route a FAIL verdict, weaker models still stall or advance incorrectly when the repo-local workflow explainer and coordinator prompt omit the recovery path.
- evidence:
  - .opencode/skills/ticket-execution/SKILL.md does not include an explicit Failure recovery paths section.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### WFLOW027

- finding_id: WFLOW027
- summary: Restart-surface tools return paths without verifying what they wrote.
- severity: error
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/tools/handoff_publish.ts
- observed_or_reproduced: When handoff and context tools only echo file paths, weaker models cannot tell whether the files were written correctly or still agree with canonical state after publication.
- evidence:
  - .opencode/tools/handoff_publish.ts does not return verification metadata alongside published restart-surface paths.
- remaining_verification_gap: None recorded beyond the validated finding scope.

### CONFIG003

- finding_id: CONFIG003
- summary: opencode.jsonc does not grant 'external_directory' permission.
- severity: warning
- evidence_grade: repo-state validation
- affected_files_or_surfaces: opencode.jsonc
- observed_or_reproduced: Without external_directory: allow, agents running in non-interactive mode cannot access system tooling paths (JDK, Godot templates, Android SDK, etc.). This causes auto-rejection of external path reads.
- evidence:
  - permission.external_directory = None
- remaining_verification_gap: None recorded beyond the validated finding scope.

### CONFIG004

- finding_id: CONFIG004
- summary: opencode.jsonc bash permissions missing common commands: ['chmod *', 'cp *', 'echo *', 'mkdir *', 'mv *', 'rm *', 'tee *', 'touch *']
- severity: warning
- evidence_grade: repo-state validation
- affected_files_or_surfaces: opencode.jsonc
- observed_or_reproduced: The template used to scaffold this repo had a limited bash allowlist. Agents need mkdir, cp, mv, etc. to create build directories and manage files.
- evidence:
  - Missing: ['chmod *', 'cp *', 'echo *', 'mkdir *', 'mv *', 'rm *', 'tee *', 'touch *']
  - Present: ['cat *', 'find *', 'git add *', 'git commit *', 'git diff*', 'git log*', 'git status*', 'head *', 'ls *', 'node *', 'npm *', 'pwd', 'pytest *', 'python *', 'python3 *', 'rg *', 'ruff *', 'sed *', 'tail *', 'uv *']
- remaining_verification_gap: None recorded beyond the validated finding scope.

### SKILL002

- finding_id: SKILL002
- summary: The repo-local `ticket-execution` skill is too thin to explain the actual lifecycle contract to weaker models.
- severity: warning
- evidence_grade: repo-state validation
- affected_files_or_surfaces: .opencode/skills/ticket-execution/SKILL.md
- observed_or_reproduced: When the local workflow explainer omits transition guidance, contradiction-stop rules, artifact ownership, or command boundaries, agents fall back to guess-and-check against the tools.
- evidence:
  - ticket-execution does not forbid expected-results-as-PASS artifact fabrication.
  - ticket-execution does not clarify that slash commands are human entrypoints, not autonomous tools.
- remaining_verification_gap: None recorded beyond the validated finding scope.

## Code Quality Findings

No execution or reference-integrity findings were detected.

## Verification Gaps

- The diagnosis pack validates the concrete failures above. It does not claim broader runtime-path coverage than the current audit and supporting evidence actually exercised.

