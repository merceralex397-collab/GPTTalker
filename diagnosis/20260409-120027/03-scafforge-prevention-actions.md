# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- source_finding: CONFIG001
- change_target: scafforge-audit diagnosis contract
- why_it_prevents_recurrence: Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-002

- source_finding: CONFIG002
- change_target: scafforge-audit diagnosis contract
- why_it_prevents_recurrence: Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-003

- source_finding: CYCLE002
- change_target: scafforge-audit diagnosis contract
- why_it_prevents_recurrence: Teach audit to stop repeated diagnosis-pack churn when the repo has no newer package or process-version change; require Scafforge package work before the next subject-repo audit.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-004

- source_finding: WFLOW010
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Regenerate derived restart surfaces from canonical manifest and workflow state after every workflow mutation so resume guidance never contradicts active bootstrap, ticket, or lease facts.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-005

- source_finding: WFLOW012
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Use one lease-ownership model everywhere: the team leader claims and releases ticket leases, specialists work under the active lease, and only Wave 0 setup work may claim before bootstrap is ready.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-006

- source_finding: WFLOW016
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Make `smoke_test` parse shell-style override commands correctly, treat leading `KEY=VALUE` tokens as environment overrides, and detect transcript-level `ENOENT` override failures as workflow-surface defects instead of generic test failures.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-007

- source_finding: WFLOW023
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Make ticket acceptance criteria scope-isolated: if the literal closeout command depends on later-ticket work, split the backlog differently or encode the dependency explicitly instead of shipping contradictory acceptance.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-008

- source_finding: WFLOW024
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Give historical reconciliation one legal evidence-backed path so superseded invalidated tickets can be repaired without depending on impossible direct-artifact or closeout assumptions.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-009

- source_finding: WFLOW027
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Return verification metadata from restart-surface tools so callers can confirm what handoff and snapshot publication actually wrote.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-010

- source_finding: CONFIG003
- change_target: scafforge-audit diagnosis contract
- why_it_prevents_recurrence: Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-011

- source_finding: CONFIG004
- change_target: scafforge-audit diagnosis contract
- why_it_prevents_recurrence: Refresh managed workflow docs, tools, and validators together so repair replaces drift instead of layering new semantics over old ones.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-012

- source_finding: SKILL002
- change_target: project-skill-bootstrap and agent-prompt-engineering surfaces
- why_it_prevents_recurrence: Make the generated `ticket-execution` skill the canonical lifecycle explainer so weaker models do not have to reverse-engineer the state machine from tool errors.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

## Validation and Test Updates

- CONFIG001: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- CONFIG002: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- CYCLE002: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW010: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW012: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW016: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW023: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW024: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW027: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- CONFIG003: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- CONFIG004: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- SKILL002: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

## Documentation or Prompt Updates

- WFLOW010: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW012: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW016: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW023: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW024: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW027: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- SKILL002: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

## Open Decisions

- None recorded.

