# Implementation: POLISH-002

## Summary
Created security regression tests for path traversal, target validation, redaction, and fail-closed behavior.

## Changes Made

### New Files
1. **tests/hub/test_security.py** - Security regression tests covering:
   - Path traversal tests (5 tests): dotdot, windows backslash, absolute path, null byte, symlink
   - Target validation tests (4 tests): unknown node, unknown repo, unregistered write target, extension allowlist
   - Redaction tests (4 tests): API key, token, password, sensitive path
   - Fail-closed tests (4 tests): missing policy engine, missing repository, invalid policy, malformed params
   - Additional edge cases (6 tests)

## Test Coverage
- 23+ security-focused test cases
- Covers all known attack vectors
- Verifies fail-closed behavior

## Acceptance Criteria
- Security regression suite covers path and target validation ✓
- Log redaction behavior is tested ✓
- Fail-closed expectations are enforced under error conditions ✓
