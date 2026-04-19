# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- source_finding: EXEC-REMED-001
- change_target: repo-scaffold-factory managed template surfaces
- why_it_prevents_recurrence: Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun the generated-tool execution smoke coverage plus the relevant GPTTalker fixture family

### ACTION-002

- source_finding: WFLOW023
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Make ticket acceptance criteria scope-isolated: if the literal closeout command depends on later-ticket work, split the backlog differently or encode the dependency explicitly instead of shipping contradictory acceptance.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-003

- source_finding: WFLOW026
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Teach the shared artifact verdict extractor to accept markdown-emphasized labels, compact `## QA PASS` / `## Review APPROVE` headings, and plain `**Overall**: PASS` labels, then route ticket_lookup and ticket_update through that single parser.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

## Validation and Test Updates

- EXEC-REMED-001: rerun the generated-tool execution smoke coverage plus the relevant GPTTalker fixture family.

- WFLOW023: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW026: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

## Documentation or Prompt Updates

- WFLOW023: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW026: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

## Open Decisions

- None recorded.

