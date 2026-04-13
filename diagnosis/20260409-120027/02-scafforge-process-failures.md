# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### CONFIG001

- linked_report_1_finding: CONFIG001
- implicated_surface: scafforge-audit diagnosis contract
- ownership_class: managed workflow contract surface
- workflow_failure: opencode.jsonc is missing the 'model' field.

### CONFIG002

- linked_report_1_finding: CONFIG002
- implicated_surface: scafforge-audit diagnosis contract
- ownership_class: managed workflow contract surface
- workflow_failure: opencode.jsonc is missing the 'default_agent' field.

### CYCLE002

- linked_report_1_finding: CYCLE002
- implicated_surface: scafforge-audit diagnosis contract
- ownership_class: audit and lifecycle diagnosis surface
- workflow_failure: Repeated diagnosis packs are re-reporting the same repair-routed findings without any intervening package or process-version change.

### WFLOW010

- linked_report_1_finding: WFLOW010
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts.

### WFLOW012

- linked_report_1_finding: WFLOW012
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.

### WFLOW016

- linked_report_1_finding: WFLOW016
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: The managed smoke-test override contract can fail before the requested smoke command even starts.

### WFLOW023

- linked_report_1_finding: WFLOW023
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: The generated lifecycle contract is not verdict-aware, so FAIL review or QA artifacts can still look advanceable.

### WFLOW024

- linked_report_1_finding: WFLOW024
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Fail-state routing is still under-specified in generated prompts or workflow skills.

### WFLOW027

- linked_report_1_finding: WFLOW027
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Restart-surface tools return paths without verifying what they wrote.

### CONFIG003

- linked_report_1_finding: CONFIG003
- implicated_surface: scafforge-audit diagnosis contract
- ownership_class: managed workflow contract surface
- workflow_failure: opencode.jsonc does not grant 'external_directory' permission.

### CONFIG004

- linked_report_1_finding: CONFIG004
- implicated_surface: scafforge-audit diagnosis contract
- ownership_class: managed workflow contract surface
- workflow_failure: opencode.jsonc bash permissions missing common commands: ['cp *', 'echo *', 'mkdir *', 'mv *', 'touch *']

### SKILL002

- linked_report_1_finding: SKILL002
- implicated_surface: project-skill-bootstrap and agent-prompt-engineering surfaces
- ownership_class: project skill or prompt surface
- workflow_failure: The repo-local `ticket-execution` skill is too thin to explain the actual lifecycle contract to weaker models.

## Ownership Classification

### CYCLE002

- ownership_class: audit and lifecycle diagnosis surface
- affected_surface: scafforge-audit diagnosis contract

### CONFIG001

- ownership_class: managed workflow contract surface
- affected_surface: scafforge-audit diagnosis contract

### CONFIG002

- ownership_class: managed workflow contract surface
- affected_surface: scafforge-audit diagnosis contract

### CONFIG003

- ownership_class: managed workflow contract surface
- affected_surface: scafforge-audit diagnosis contract

### CONFIG004

- ownership_class: managed workflow contract surface
- affected_surface: scafforge-audit diagnosis contract

### WFLOW010

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW012

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW016

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW023

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW024

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW027

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### SKILL002

- ownership_class: project skill or prompt surface
- affected_surface: project-skill-bootstrap and agent-prompt-engineering surfaces

## Root Cause Analysis

### CONFIG001

- root_cause: The template used to scaffold this repo did not include a model assignment, or repair has not yet propagated the updated template.
- safer_target_pattern: opencode.jsonc must contain a top-level 'model' field in provider/model format (e.g. 'minimax-coding-plan/MiniMax-M2.7').
- how_the_workflow_allowed_it: opencode.jsonc is missing the 'model' field.

### CONFIG002

- root_cause: The template used to scaffold this repo did not include a default_agent assignment. Without this, opencode falls back to the built-in 'build' agent instead of the project's team-leader.
- safer_target_pattern: opencode.jsonc must contain a top-level 'default_agent' field pointing to the team-leader agent (e.g. 'myproject-team-leader').
- how_the_workflow_allowed_it: opencode.jsonc is missing the 'default_agent' field.

### CYCLE002

- root_cause: Audit kept producing new diagnosis packs even though the repo had no later Scafforge repair or workflow-contract change after the latest diagnosis. That creates audit churn instead of new decision-making evidence.
- safer_target_pattern: Stop rerunning subject-repo audit until Scafforge package work changes the managed workflow contract or process version, then rerun one fresh audit against the updated package.
- how_the_workflow_allowed_it: Repeated diagnosis packs are re-reporting the same repair-routed findings without any intervening package or process-version change.

### WFLOW010

- root_cause: `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are not being regenerated from `tickets/manifest.json`, `.opencode/state/workflow-state.json`, and `.opencode/meta/pivot-state.json` after workflow mutations or managed repair, leaving bootstrap, repair-follow-on, pivot, verification, lane-lease, or active-ticket state stale.
- safer_target_pattern: Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest, workflow state, and pivot state after every workflow save, compute handoff readiness from bootstrap plus repair-follow-on plus verification state in one shared contract, and fail repair verification if any derived restart surface drifts.
- how_the_workflow_allowed_it: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts.

### WFLOW012

- root_cause: Some workflow docs and prompts still describe worker-owned lease claims while others expect the team leader to coordinate claims. That contradiction is enough to make weaker models thrash around ticket ownership and pre-bootstrap write rules.
- safer_target_pattern: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.
- how_the_workflow_allowed_it: The generated lease-ownership contract is split across coordinator and worker surfaces, so agents can disagree about who should claim a ticket and when bootstrap gates apply.

### WFLOW016

- root_cause: The generated `smoke_test` tool passes `command_override` directly into `spawn()` argv and does not separate shell-style environment assignments like `UV_CACHE_DIR=...` from the executable. Valid repo-standard override commands can therefore misfire as `ENOENT` instead of running the intended smoke check.
- safer_target_pattern: Parse one-item shell-style overrides into argv, treat leading `KEY=VALUE` tokens as environment overrides, and report malformed overrides as configuration errors instead of misclassifying them as runtime environment failures.
- how_the_workflow_allowed_it: The managed smoke-test override contract can fail before the requested smoke command even starts.

### WFLOW023

- root_cause: Transition guidance and transition enforcement must inspect artifact verdicts, not just artifact existence. Otherwise weaker models continue on the happy path after blocker findings.
- safer_target_pattern: Extract verdicts from the latest review and QA artifacts, route FAIL or BLOCKED outcomes back to implementation, and reject lifecycle transitions when the latest artifact verdict is blocking or unclear.
- how_the_workflow_allowed_it: The generated lifecycle contract is not verdict-aware, so FAIL review or QA artifacts can still look advanceable.

### WFLOW024

- root_cause: Even if the tool contract knows how to route a FAIL verdict, weaker models still stall or advance incorrectly when the repo-local workflow explainer and coordinator prompt omit the recovery path.
- safer_target_pattern: Document review, QA, smoke-test, and bootstrap failure recovery paths in ticket-execution, and instruct the team leader to follow transition_guidance.recovery_action whenever it is present.
- how_the_workflow_allowed_it: Fail-state routing is still under-specified in generated prompts or workflow skills.

### WFLOW027

- root_cause: When handoff and context tools only echo file paths, weaker models cannot tell whether the files were written correctly or still agree with canonical state after publication.
- safer_target_pattern: Return verified flags plus current workflow metadata for published restart surfaces and include size or hash metadata for snapshots so callers can confirm what was written.
- how_the_workflow_allowed_it: Restart-surface tools return paths without verifying what they wrote.

### CONFIG003

- root_cause: Without external_directory: allow, agents running in non-interactive mode cannot access system tooling paths (JDK, Godot templates, Android SDK, etc.). This causes auto-rejection of external path reads.
- safer_target_pattern: Add '"external_directory": "allow"' to the permission block in opencode.jsonc.
- how_the_workflow_allowed_it: opencode.jsonc does not grant 'external_directory' permission.

### CONFIG004

- root_cause: The template used to scaffold this repo had a limited bash allowlist. Agents need mkdir, cp, mv, etc. to create build directories and manage files.
- safer_target_pattern: Add the missing commands to the bash permission allowlist in opencode.jsonc.
- how_the_workflow_allowed_it: opencode.jsonc bash permissions missing common commands: ['cp *', 'echo *', 'mkdir *', 'mv *', 'touch *']

### SKILL002

- root_cause: When the local workflow explainer omits transition guidance, contradiction-stop rules, artifact ownership, or command boundaries, agents fall back to guess-and-check against the tools.
- safer_target_pattern: Keep `ticket-execution` narrowly procedural: route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle contradictions, reserve `smoke_test` as the only PASS producer, and keep slash commands human-only.
- how_the_workflow_allowed_it: The repo-local `ticket-execution` skill is too thin to explain the actual lifecycle contract to weaker models.

