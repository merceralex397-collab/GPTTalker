# REPO-001: inspect_repo_tree tool

## Summary

Implement the inspect_repo_tree MCP tool that allows ChatGPT to browse repository directory structures. The hub routes tree listing requests to the appropriate node agent, which performs local filesystem enumeration. Support both immediate (single-level) and recursive tree listings with binary file detection and .gitignore respect.

## Stage

planning

## Status

todo

## Depends On

- CORE-003
- CORE-004

## Acceptance Criteria

- [ ] inspect_repo_tree MCP tool accepts repo alias, optional path, and depth parameter
- [ ] Immediate mode: list direct children of a directory
- [ ] Recursive mode: full tree up to configurable max depth
- [ ] Node agent endpoint performs local filesystem enumeration
- [ ] Binary files detected and marked (not listed as text)
- [ ] .gitignore patterns respected (skip ignored files/dirs)
- [ ] Response includes: name, type (file/dir), size, path for each entry
- [ ] Large directory truncation with item count and truncation flag
- [ ] Path validation: must be within repo root (no traversal)
- [ ] Unit tests and integration test with mock filesystem

## Artifacts

- None yet

## Notes

- Use pathlib on node agent for cross-platform path handling
- .gitignore parsing can use pathspec library or gitignore_parser
- Max depth default: 3 for recursive, to prevent enormous responses
- Consider adding a file count summary for truncated results
