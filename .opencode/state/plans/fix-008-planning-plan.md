# Plan: FIX-008 - Add recent_commits to git_status

## Summary
Add recent_commits field to git_status output.

## Files
- src/node_agent/executor.py: Add git log command
- src/hub/tools/git_operations.py: Add to response
- tests: Update test expectations

## Acceptance
- [ ] recent_commits array in response
- [ ] Each commit has hash, author, date, message
- [ ] Default 10 commits
