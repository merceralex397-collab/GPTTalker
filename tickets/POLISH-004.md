# POLISH-004: Scheduled indexing

## Summary

Implement scheduled context refresh that automatically re-indexes repositories on a configurable interval. Add stale detection to identify repos whose context is outdated relative to recent changes, and trigger re-indexing as needed. This ensures the semantic search context stays fresh without manual intervention.

## Stage

planning

## Status

blocked

## Depends On

- CTX-002

## Acceptance Criteria

- [ ] Background scheduler for periodic indexing (asyncio task or APScheduler)
- [ ] Configurable interval per repo (default: 6 hours)
- [ ] Global interval override in hub configuration
- [ ] Stale detection: compare last_indexed timestamp with repo's latest commit time
- [ ] Auto re-index when staleness exceeds threshold
- [ ] Scheduler status endpoint: next run, last run, repos pending
- [ ] Skip indexing if repo unchanged since last index
- [ ] Concurrent indexing limit to prevent resource exhaustion
- [ ] Scheduler enable/disable via config and runtime toggle
- [ ] Logging of all scheduled indexing runs
- [ ] Unit tests for stale detection and scheduling logic

## Artifacts

- None yet

## Notes

- asyncio background task is simplest; APScheduler adds cron-style flexibility
- Stale detection via git rev-parse HEAD comparison is lightweight
- Consider jittering scheduled runs to avoid all repos indexing simultaneously
- Runtime toggle useful for maintenance windows
