# REPO-002: read_repo_file tool

## Summary

Implement the read_repo_file MCP tool that allows ChatGPT to read individual files from registered repositories. The node agent reads the file locally and returns its content with metadata. Handle large files via truncation, detect binary files (returning metadata only), and perform text encoding detection for non-UTF-8 files.

## Stage

planning

## Status

todo

## Depends On

- CORE-003
- CORE-004

## Acceptance Criteria

- [ ] read_repo_file MCP tool accepts repo alias and file path
- [ ] Node agent reads file and returns content with metadata
- [ ] Metadata: size, extension, modified_time, encoding, line_count
- [ ] Large file truncation at configurable limit (default 100KB) with truncation flag
- [ ] Binary file detection returns metadata only (no content)
- [ ] Text encoding detection (UTF-8, Latin-1, etc.) with re-encoding to UTF-8
- [ ] Path validation: must be within repo root, no traversal
- [ ] File not found returns structured error (not 500)
- [ ] Optional line range parameter (start_line, end_line)
- [ ] Unit tests for truncation, binary detection, encoding handling

## Artifacts

- None yet

## Notes

- Use python-magic or simple heuristic for binary detection (null byte check)
- charset-normalizer or chardet for encoding detection
- Line range is useful for ChatGPT to read specific sections of large files
- Consider returning content hash for cache validation
