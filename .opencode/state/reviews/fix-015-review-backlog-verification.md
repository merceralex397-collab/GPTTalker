# Backlog Verification — FIX-015

## Ticket
- **ID:** FIX-015
- **Title:** Fix Task UUID handling and CLI entrypoint packaging
- **Stage:** closeout
- **Status:** done
- **Verification state:** PASS

## Verification Summary
Two issues fixed:
1. **UUID handling:** `TaskRepository._row_to_task` now handles both UUID and string task_ids with try/except fallback; `TaskRecord.task_id` type updated to `UUID | str`
2. **CLI packaging:** `scripts/*` added to `pyproject.toml` package discovery `include` list

## Evidence
1. **UUID handling:** `_row_to_task` uses try/except to parse UUID; string IDs fall back to string
2. **CLI packaging:** `scripts/*.py` entrypoints now discoverable after `pip install`

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| TaskRepository handles both UUID and string task_ids without crashing | PASS |
| CLI entrypoints work after pip install | PASS |
| Package discovery includes scripts/ | PASS |

## Notes
- No follow-up ticket needed
