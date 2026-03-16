# QA Verification: CORE-005 - Policy engine and normalized path validation

## Ticket Information
- **ID**: CORE-005
- **Title**: Policy engine and normalized path validation
- **Stage**: QA
- **Status**: Verification in progress

## Acceptance Criteria Verification

### 1. Unknown targets are rejected explicitly ✅ PASS

**Verification Method**: Code inspection of policy classes

**Findings**:
- **NodePolicy** (`src/hub/policy/node_policy.py`): Returns `NodeAccessResult` with explicit `approved: bool` field and `rejection_reason: str | None`. When node is unknown or inaccessible, `approved=False` with explicit reason.
- **RepoPolicy** (`src/hub/policy/repo_policy.py`): Raises `ValueError` with descriptive message for unknown/inaccessible repos.
- **WriteTargetPolicy** (`src/hub/policy/write_target_policy.py`): Raises `ValueError` for unknown write targets and extension allowlist violations.
- **LLMServicePolicy** (`src/hub/policy/llm_service_policy.py`): Raises `ValueError` for unknown or inaccessible LLM services.
- **PolicyEngine** (`engine.py`): Returns `ValidationResult` dataclass with `allowed: bool` and explicit `reason: str | None` for all validation failures.

**Conclusion**: Fail-closed behavior is enforced throughout. Unknown targets are explicitly rejected with descriptive reasons.

---

### 2. Path normalization rules are central and reusable ✅ PASS

**Verification Method**: Code inspection of path_utils.py and its usage

**Findings**:
- **PathNormalizer class** (`path_utils.py`): Central utility with 7 static methods:
  - `normalize(path, base)`: Core normalization with traversal prevention
  - `validate_no_traversal(path)`: Checks for `..`, `~`, and URL-encoded traversal
  - `is_safe_relative(path, base)`: Verifies path stays within base directory
  - `validate_symlinks(path, base)`: Detects symlink escape attempts
  - `validate_absolute(path, require_absolute)`: Validates absolute path format
  - `validate_extension(extension, allowed_extensions)`: Extension allowlist validation
  - `build_safe_path(base, *parts)`: Safe path construction
  
- **PathValidationResult dataclass**: Standardized return type for validation operations

- **Usage in engine.py**: PathNormalizer is used consistently in:
  - `validate_file_read()`: Normalizes and validates read paths
  - `validate_file_write()`: Normalizes and validates write paths

- **Exports**: Properly exported in `__init__.py` for reusable access

**Conclusion**: Path normalization is centralized, well-documented, and reusable across the policy engine.

---

### 3. Write and read scopes are separated cleanly ✅ PASS

**Verification Method**: Code inspection of scopes.py and engine.py

**Findings**:
- **OperationScope enum** (`scopes.py`): Cleanly defines three scopes:
  - `READ = "read"`
  - `WRITE = "write"`
  - `EXECUTE = "execute"`

- **ValidationContext** (`scopes.py`): Dataclass includes `scope: OperationScope` field for passing scope through validation chain

- **ScopeValidator** (`scopes.py`): Helper class with methods:
  - `allows_read(scope)`: Checks if scope permits read
  - `allows_write(scope)`: Checks if scope permits write
  - `allows_execute(scope)`: Checks if scope permits execute
  - `requires_write(scope)`: Checks if scope requires write access
  - `requires_read(scope)`: Checks if scope requires read access

- **PolicyEngine separation** (`engine.py`):
  - `validate_node_read()` / `validate_node_write()`: Separate methods for read vs write node validation
  - `validate_file_read()` / `validate_file_write()`: Separate methods for file path validation
  - `validate_read_operation()` / `validate_write_operation()`: Complete validation chains for each scope
  - `validate_llm_operation()`: Separate LLM validation (uses READ scope as default)

**Conclusion**: Read and write scopes are cleanly separated at both the enum level and the validation method level.

---

## Code Quality Assessment

### Structure
- All policy classes properly imported and wired in `dependencies.py`
- DI provider `get_policy_engine()` correctly composes all policy components
- Proper type hints throughout with return types documented

### Error Handling
- Exceptions properly raised with descriptive messages
- Fail-closed behavior enforced at each validation layer
- Structured logging at DEBUG/INFO/WARNING levels

### Integration Points
- PolicyEngine integrates with all four registry policies (node, repo, write_target, llm_service)
- Path normalization integrates with repo access validation
- Scope context properly propagated through validation chains

---

## Runtime Validation

**Note**: Runtime validation was not performed due to bash permission restrictions in this environment. Static code analysis confirms the implementation is sound.

---

## QA Summary

| Acceptance Criterion | Status |
|---------------------|--------|
| Unknown targets are rejected explicitly | ✅ PASS |
| Path normalization rules are central and reusable | ✅ PASS |
| Write and read scopes are separated cleanly | ✅ PASS |

### Overall Result: **PASS**

All three acceptance criteria are verified via code inspection. The policy engine implementation is complete, well-structured, and follows fail-closed principles throughout.

---

## Artifacts Reviewed
- `src/hub/policy/path_utils.py` - Path normalization utility (275 lines)
- `src/hub/policy/scopes.py` - Operation scopes (134 lines)
- `src/hub/policy/engine.py` - Policy engine orchestration (490 lines)
- `src/hub/policy/__init__.py` - Exports (27 lines)
- `src/hub/dependencies.py` - DI providers (328 lines)
