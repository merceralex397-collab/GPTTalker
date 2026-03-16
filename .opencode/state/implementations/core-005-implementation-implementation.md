# CORE-005 Implementation: Policy Engine and Normalized Path Validation

## Summary

Successfully implemented the fail-closed policy engine and centralized path normalization utility. This work integrates the individual policy classes from CORE-001/CORE-002 into a unified validation chain.

## Files Created

### 1. `src/hub/policy/path_utils.py` - Path Normalization Utility

Created `PathNormalizer` class with the following capabilities:
- **normalize()**: Normalizes paths relative to a base directory, rejecting traversal attempts
- **validate_no_traversal()**: Checks for path traversal patterns (`..`, `~`, URL-encoded)
- **is_safe_relative()**: Verifies path stays within base directory
- **validate_symlinks()**: Validates paths don't escape via symlink resolution
- **validate_absolute()**: Validates paths are absolute when required
- **validate_extension()**: Validates file extensions against allowlists
- **build_safe_path()**: Convenience method for constructing safe paths

Also created `PathValidationResult` dataclass to return validation results with normalized path, validity status, and error messages.

### 2. `src/hub/policy/scopes.py` - Operation Scope Definitions

Created:
- **OperationScope** enum: READ, WRITE, EXECUTE for operation type classification
- **ValidationContext** dataclass: Contains scope, trace_id, and caller information
- **ScopeValidator** class: Helper methods for scope-based access control decisions

### 3. `src/hub/policy/engine.py` - Policy Engine Orchestration

Created `PolicyEngine` class that combines all policies into a unified validation chain:

**Read Operation Validators:**
- `validate_node_read()`: Node access for reads
- `validate_repo_read()`: Repository access for reads
- `validate_file_read()`: File path validation for reads

**Write Operation Validators:**
- `validate_node_write()`: Node access for writes
- `validate_write_target()`: Write target and extension validation
- `validate_file_write()`: Complete file write validation chain

**LLM Operation Validators:**
- `validate_llm_service()`: LLM service access by ID
- `validate_llm_service_by_name()`: LLM service access by name

**Combined Validation Chains:**
- `validate_read_operation()`: Full read validation with node, repo, and file checks
- `validate_write_operation()`: Full write validation with node and target checks
- `validate_llm_operation()`: Full LLM service validation

## Files Modified

### 4. `src/hub/policy/__init__.py`

Updated exports to include all new components:
- `PathNormalizer`, `PathValidationResult`
- `OperationScope`, `ValidationContext`
- `PolicyEngine`, `ValidationResult`
- Re-exported existing policies

### 5. `src/hub/dependencies.py`

Added DI provider:
- `get_policy_engine()`: Creates PolicyEngine with all policy dependencies injected

### 6. `src/hub/transport/__init__.py` (Bug Fix)

Fixed pre-existing import error:
- Removed non-existent `MCPTransport` from imports (was `TransportProtocol`)

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Unknown targets are rejected explicitly | ✅ | PolicyEngine returns clear rejection reasons via ValidationResult with explicit reason strings |
| Path normalization rules are central and reusable | ✅ | PathNormalizer in policy/path_utils.py with static methods; used by PolicyEngine |
| Write and read scopes are separated cleanly | ✅ | Separate validate_read_operation() and validate_write_operation() methods; OperationScope enum |

## Technical Details

- All new files use Python 3.11+ type hints
- Dataclasses used for result types (PathValidationResult, ValidationResult, ValidationContext)
- Fail-closed behavior: unknown nodes/repos/services → explicit rejection with reason
- Integration with existing NodePolicy, RepoPolicy, WriteTargetPolicy, LLMServicePolicy
- Structured logging with trace_id context
- All lint checks pass (`ruff check`)

## Integration Points

The PolicyEngine is now ready for CORE-006 (MCP tool routing framework) to call:
- Tool router will use `PolicyEngine.validate_read_operation()` for repo inspection tools
- Tool router will use `PolicyEngine.validate_write_operation()` for markdown delivery
- Tool router will use `PolicyEngine.validate_llm_operation()` for LLM routing

## Validation

- ✅ `ruff check src/hub/policy/` - All checks passed
- ✅ `ruff check src/hub/dependencies.py` - All checks passed
- ✅ AST parsing - All files parse correctly

## Notes

- The pre-existing circular import issue in the hub was temporarily addressed to allow testing
- The PolicyEngine delegates to existing policy classes, maintaining their existing behavior
- All rejection paths include structured logging with trace_id support
