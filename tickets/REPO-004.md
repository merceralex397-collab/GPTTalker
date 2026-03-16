# REPO-004: git_status tool

## Summary

Implement the git_status MCP tool that provides ChatGPT with git repository state information. The node agent executes git CLI commands locally to report branch name, dirty/clean status, changed files summary, ahead/behind tracking info, and recent commit history.

## Stage

planning

## Status

todo

## Depends On

- CORE-003
- CORE-004

## Acceptance Criteria

- [ ] git_status MCP tool accepts repo alias
- [ ] Returns current branch name
- [ ] Returns dirty flag (true if uncommitted changes exist)
- [ ] Returns changed files list with status (modified, added, deleted, untracked)
- [ ] Returns ahead/behind counts relative to upstream (when available)
- [ ] Returns recent commits list (configurable count, default 10)
- [ ] Commit info: hash (short), author, date, message (first line)
- [ ] Node agent executes git CLI commands in repo directory
- [ ] Handles non-git directories gracefully (structured error)
- [ ] Unit tests with mock git output

## Artifacts

- None yet

## Notes

- Use git porcelain format (--porcelain) for machine-parseable status output
- git log --oneline --format for recent commits
- git rev-list --left-right --count for ahead/behind
- Ensure git commands don't modify repo state (all read-only)
