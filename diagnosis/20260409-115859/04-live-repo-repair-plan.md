# Live Repo Repair Plan

## Preconditions

- Repo: /home/pc/projects/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Triage Order

- package_first_count: 1
- subject_repo_follow_up_count: 0
- host_or_manual_prerequisite_count: 1

## Repeated Failure Note

- This repo has already gone through at least one audit-to-repair cycle and still reproduces workflow-layer findings.
- Before another repair run, compare the latest previous diagnosis pack against repair history and explain why those findings survived.
- Do not keep rerunning subject-repo audit until a Scafforge package or process-version change exists.

## Package Changes Required First

### REMED-002

- linked_report_id: CYCLE002
- action_type: Scafforge package work required before the next subject-repo run
- requires_scafforge_repair_afterward: no, not until the package or host prerequisite gap is resolved
- carry_diagnosis_pack_into_scafforge_first: yes
- target_repo: Scafforge package repo
- summary: Stop rerunning subject-repo audit until Scafforge package work changes the managed workflow contract or process version, then rerun one fresh audit against the updated package.

## Post-Update Repair Actions

- Route 8 workflow-layer finding(s) into `scafforge-repair` for deterministic managed-surface refresh.

- After deterministic repair, rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

### REMED-001

- linked_report_id: CONFIG001
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Run scafforge-repair to regenerate opencode.jsonc from the current template.

### REMED-003

- linked_report_id: WFLOW010
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest, workflow state, and pivot state after every workflow save, compute handoff readiness from bootstrap plus repair-follow-on plus verification state in one shared contract, and fail repair verification if any derived restart surface drifts.

### REMED-004

- linked_report_id: WFLOW012
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Adopt one lease model everywhere: the team leader owns `ticket_claim` and `ticket_release`, specialists work only inside the already-active ticket lease, and only Wave 0 setup work may claim before bootstrap is ready.

### REMED-005

- linked_report_id: WFLOW016
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Parse one-item shell-style overrides into argv, treat leading `KEY=VALUE` tokens as environment overrides, and report malformed overrides as configuration errors instead of misclassifying them as runtime environment failures.

### REMED-006

- linked_report_id: WFLOW023
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Extract verdicts from the latest review and QA artifacts, route FAIL or BLOCKED outcomes back to implementation, and reject lifecycle transitions when the latest artifact verdict is blocking or unclear.

### REMED-007

- linked_report_id: WFLOW024
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Document review, QA, smoke-test, and bootstrap failure recovery paths in ticket-execution, and instruct the team leader to follow transition_guidance.recovery_action whenever it is present.

### REMED-008

- linked_report_id: WFLOW027
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Return verified flags plus current workflow metadata for published restart surfaces and include size or hash metadata for snapshots so callers can confirm what was written.

### REMED-009

- linked_report_id: SKILL002
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Keep `ticket-execution` narrowly procedural: route from `ticket_lookup.transition_guidance`, stop after repeated lifecycle contradictions, reserve `smoke_test` as the only PASS producer, and keep slash commands human-only.

## Ticket Follow-Up

- No subject-repo ticket follow-up was recommended from the current diagnosis run.

## Reverification Plan

- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.
- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.
- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.

