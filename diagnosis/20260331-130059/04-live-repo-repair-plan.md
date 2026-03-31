# Live Repo Repair Plan

## Preconditions

- Repo: /home/rowan/GPTTalker
- Audit stayed non-mutating. No repo or product-code edits were made by this diagnosis run.

## Package Changes Required First

### REMED-002

- linked_report_id: ENV003
- action_type: host prerequisite or operator follow-up
- requires_scafforge_repair_afterward: no, not until the package or host prerequisite gap is resolved
- carry_diagnosis_pack_into_scafforge_first: yes
- target_repo: subject repo host environment
- summary: Configure git identity on the host used for audit or repair, or mark the affected verification as blocked by environment rather than as a clean or source-level result.

## Post-Update Repair Actions

- Route 1 workflow-layer finding(s) into `scafforge-repair` for deterministic managed-surface refresh.

- After deterministic repair, rerun project-local skill regeneration, agent-team follow-up, and prompt hardening before handoff.

### REMED-003

- linked_report_id: SKILL001
- action_type: safe Scafforge package change
- should_scafforge_repair_run: yes
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Populate every baseline local skill with concrete repo-specific rules and validation commands; generated `.opencode/skills/` files must not retain template filler.

## Ticket Follow-Up

### REMED-001

- linked_report_id: EXEC001
- action_type: generated-repo remediation ticket/process repair
- should_scafforge_repair_run: only after managed workflow repair converges
- carry_diagnosis_pack_into_scafforge_first: no
- target_repo: subject repo
- summary: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.

## Reverification Plan

- After package-side fixes land, run one fresh audit on the subject repo before applying another repair cycle.
- After managed repair, rerun the public repair verifier and confirm restart surfaces, ticket routing, and any historical trust restoration paths match the current canonical state.
- Do not treat restart prose alone as proof; the canonical manifest and workflow state remain the source of truth.

