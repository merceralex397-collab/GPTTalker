# REPO-003: search_repo tool

## Summary

Implement the search_repo MCP tool that allows ChatGPT to search within repositories for text patterns, file paths, and symbols. The node agent executes ripgrep (rg) for fast text search and provides path-based search and best-effort symbol search. Results are chunked for large result sets to fit within MCP response limits.

## Stage

planning

## Status

todo

## Depends On

- CORE-003
- CORE-004

## Acceptance Criteria

- [ ] search_repo MCP tool accepts repo alias, query, and search mode
- [ ] Text search mode: full-text search via ripgrep on node agent
- [ ] Path search mode: find files by name/glob pattern
- [ ] Symbol search mode: best-effort grep for function/class definitions
- [ ] Node agent executes rg subprocess with appropriate flags
- [ ] Result format: file path, line number, matched line, context lines
- [ ] Result chunking: max N results per response with total count and has_more flag
- [ ] Case-sensitive and case-insensitive search support
- [ ] File type filter support (e.g., only .py files)
- [ ] Path validation: search confined to repo root
- [ ] Unit tests with sample repo content

## Artifacts

- None yet

## Notes

- ripgrep must be installed on node machines (document as prerequisite)
- Symbol search can use rg with patterns like "def \w+", "class \w+" per language
- Default chunk size: 20 results to keep responses manageable
- Consider --max-count flag to limit ripgrep output
