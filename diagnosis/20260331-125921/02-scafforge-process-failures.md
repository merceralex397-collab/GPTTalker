# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### EXEC001

- linked_report_1_finding: EXEC001
- implicated_surface: generated repo implementation and validation surfaces
- ownership_class: generated repo execution surface
- workflow_failure: One or more Python packages fail to import — the service cannot start.

### ENV003

- linked_report_1_finding: ENV003
- implicated_surface: scafforge-audit and scafforge-repair host verification plus prerequisite-classification surfaces
- ownership_class: host prerequisite or package boundary
- workflow_failure: Git identity is not configured for this host, but the repo's tests or workflow expect commit-producing validation.

## Ownership Classification

### EXEC001

- ownership_class: generated repo execution surface
- affected_surface: generated repo implementation and validation surfaces

### ENV003

- ownership_class: host prerequisite or package boundary
- affected_surface: scafforge-audit and scafforge-repair host verification plus prerequisite-classification surfaces

## Root Cause Analysis

### EXEC001

- root_cause: Runtime errors (NameError, FastAPIError, missing dependency, broken DI pattern, etc.) that are invisible to static analysis prevent module load. Common causes: TYPE_CHECKING-guarded names used in runtime annotations, FastAPI dependency functions with non-Pydantic parameter types, circular imports.
- safer_target_pattern: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.
- how_the_workflow_allowed_it: One or more Python packages fail to import — the service cannot start.

### ENV003

- root_cause: Some repo validations rely on creating commits or reading recent commit history. Without `user.name` and `user.email`, those checks fail for host-environment reasons and can be misread as product regressions.
- safer_target_pattern: Configure git identity on the host used for audit or repair, or mark the affected verification as blocked by environment rather than as a clean or source-level result.
- how_the_workflow_allowed_it: Git identity is not configured for this host, but the repo's tests or workflow expect commit-producing validation.

