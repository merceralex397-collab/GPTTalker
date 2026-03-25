# Backlog Verification — FIX-009

## Ticket
- **ID:** FIX-009
- **Title:** Align write_markdown interface with spec contract
- **Stage:** closeout
- **Status:** done
- **Verification state:** NEEDS_FOLLOW_UP

## Verification Summary
This ticket was closed at the time with the understanding that parameter names had been aligned with the spec. However, EXEC-005 later discovered that the test contract uses different parameter names (`node_id`/`repo_id`/`path`) than what FIX-009 implemented (`node`/`write_target`/`relative_path`). EXEC-005 reverted the parameter names to match the test contract.

## The Conflict
- **FIX-009 intent:** Align with canonical brief spec (`node`/`write_target`/`relative_path`/`create_or_overwrite`)
- **EXEC-005 reality:** Tests use `node_id`/`repo_id`/`path` — EXEC-005 reverted to test contract to make tests pass
- **Result:** Parameter naming authority is ambiguous — neither spec nor tests authoritatively declare the correct names

## What's Preserved from FIX-009
1. `mode` parameter with `create_or_overwrite` and `no_overwrite` options ✅
2. `created` flag in response ✅
3. `get(target_id)` method added to `WriteTargetPolicy` ✅

## What Was Reverted
Parameter names were reverted from `node`/`write_target`/`relative_path` back to `node_id`/`repo_id`/`path` to match the test contract.

## Recommended Follow-up
**FIX-018:** Clarify write_markdown parameter naming authority — determine whether spec or tests are the source of truth, then update the losing side accordingly.

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| write_markdown accepts mode parameter | PASS |
| Parameter names align with spec | PARTIAL — conflict with EXEC-005 |
| Existing atomic write and SHA256 verification logic preserved | PASS |

## Notes
- This is not a code defect — both FIX-009 and EXEC-005 made correct changes within their understanding
- The conflict is a naming authority ambiguity that requires a product decision
- Follow-up ticket FIX-018 has been created to resolve this
