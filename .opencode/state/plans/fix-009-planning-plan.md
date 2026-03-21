# Plan: FIX-009 - Align write_markdown interface with spec contract

## Summary
Align write_markdown tool parameters with spec contract and add mode parameter.

## Changes Needed

### Parameter renaming:
- `node_id` → `node`
- `repo_id` → `write_target` (using target_id lookup)
- `path` → `relative_path`

### Add mode parameter:
- `create_or_overwrite` (default): Always write
- `no_overwrite`: Fail if file exists

### Response format:
- Add `created` flag: true if file newly created, false if overwritten

## Files
1. src/hub/tools/markdown.py: Rename params, add mode, handle response
2. src/hub/tools/__init__.py: Update schema
3. src/hub/services/node_client.py: Add mode param
4. src/node_agent/routes/operations.py: Add mode to request
5. src/node_agent/executor.py: Implement mode logic, return created flag
6. src/shared/policies/write_target_policy.py: Add get(target_id) method

## Acceptance
- [ ] mode parameter works (create_or_overwrite, no_overwrite)
- [ ] Parameter names align with spec
- [ ] Atomic write preserved
- [ ] created/updated flag in response
