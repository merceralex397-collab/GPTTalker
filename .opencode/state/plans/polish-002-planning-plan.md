# Planning: POLISH-002

## Ticket
- **ID**: POLISH-002
- **Title**: Security regression tests and redaction hardening
- **Wave**: 6
- **Lane**: qa

## Summary
Harden the security and observability surfaces with targeted regression tests for path traversal, secret redaction, and fail-closed behavior.

## Acceptance Criteria
1. Security regression suite covers path and target validation
2. Log redaction behavior is tested
3. Fail-closed expectations are enforced under error conditions

## Dependencies
- CORE-005 (Policy engine and normalized path validation)
- OBS-001 (Task history, generated-doc log, and audit schema)
- POLISH-001 (Contract tests)

## Analysis

### Background
POLISH-001 added general contract tests. POLISH-002 focuses specifically on security hardening through regression tests.

### Test Categories

1. **Path Traversal Tests**
   - ../
   - ..\\ (Windows)
   - /etc/passwd style absolute paths
   - Null byte injection
   - Symbolic link traversal

2. **Target Validation Tests**
   - Unknown node access
   - Unknown repo access
   - Unregistered write targets
   - Extension allowlist bypass attempts

3. **Redaction Tests**
   - API key redaction in logs
   - Token redaction in traces
   - Password redaction
   - Sensitive path redaction

4. **Fail-Closed Tests**
   - Missing policy engine
   - Missing repositories
   - Invalid policy requirements
   - Malformed parameters

### Implementation Plan
1. Create tests/hub/test_security.py
2. Add path traversal regression tests
3. Add redaction verification tests
4. Add fail-closed behavior tests

## Validation
- Path validation tests cover all known attack vectors
- Redaction tests verify no secrets in logs
- Fail-closed tests verify security boundaries
