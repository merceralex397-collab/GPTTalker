# Implementation Plan: FIX-005 - Fix structured logger TypeError and HubConfig attribute error

## Ticket Summary

Two bugs:
1. Structured logger TypeError: `get_logger()` returns standard `logging.Logger` but modules call `logger.info(..., key=value)` expecting structured logging
2. HubConfig attribute error: `HubConfig` defines `database_url` but code references `database_path`

## Issue Analysis

### Issue 1: Structured Logger
The codebase already has a proper `StructuredLogger` class in `src/shared/logging.py` that correctly handles **kwargs. The fix is to have `get_logger()` return `StructuredLogger` instead of `logging.Logger`.

### Issue 2: HubConfig
HubConfig is missing a `database_path` property that other code expects.

## Proposed Fix

### Issue 1: Fix get_logger()
Modify `get_logger()` in `src/shared/logging.py` to return `StructuredLogger` instead of `logging.Logger`.

### Issue 2: Add database_path property
Add `database_path` property to HubConfig in `src/hub/config.py`.

## Implementation Steps

1. Modify `get_logger()` to return `StructuredLogger`
2. Add `database_path` property to HubConfig
3. Verify hub startup and logging work

## Acceptance Criteria

- [ ] Structured logging calls with extra kwargs do not raise TypeError
- [ ] Hub startup completes without AttributeError on database_path
- [ ] Log output includes structured fields (tool_name, trace_id, etc.)

## Risk Assessment
- Risk level: Low
- Impact: Fixes blocking startup issues
