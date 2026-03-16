# WRITE-001: write_markdown tool

## Summary

Implement the write_markdown MCP tool that allows ChatGPT to create or overwrite markdown files in approved write targets. Enforce the extension allowlist, perform atomic writes (temp file + rename) to prevent partial writes, log all write operations with content hashes, and support a no-overwrite safety mode.

## Stage

planning

## Status

todo

## Depends On

- CORE-003
- CORE-005

## Acceptance Criteria

- [ ] write_markdown MCP tool accepts write target name, file path, and content
- [ ] Extension allowlist enforced (reject non-allowed extensions)
- [ ] Path validation: file must be within write target root, no traversal
- [ ] Atomic writes: write to temp file, then rename to target path
- [ ] Parent directories created automatically if needed
- [ ] Content hash (SHA-256) computed and logged
- [ ] Write operation logged in database (target, path, hash, timestamp, trace_id)
- [ ] No-overwrite mode: refuse to overwrite existing files when flag set
- [ ] Node agent performs the actual file write
- [ ] Response includes: written path, content hash, bytes written
- [ ] Unit tests for validation, atomic write, and no-overwrite logic

## Artifacts

- None yet

## Notes

- This is a security-critical path — defense in depth with checks at hub AND node agent
- Atomic write prevents corruption if process dies mid-write
- Content hash enables deduplication and audit trail
- Consider triggering re-indexing after write (future CTX-002 integration)
