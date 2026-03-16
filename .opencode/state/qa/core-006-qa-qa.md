# QA Verification: CORE-006 - MCP Tool Routing Framework

**Ticket**: CORE-006  
**Title**: MCP tool routing framework  
**Stage**: QA  
**Date**: 2026-03-16

---

## Acceptance Criteria Verification

### 1. Tool Registration Boundary ✓

**Criterion**: Tool registration boundary is defined

**Verification**:
- `PolicyRequirement` dataclass defined in `src/hub/tool_routing/requirements.py` (lines 41-127)
- `ToolDefinition` updated with `policy: PolicyRequirement | None` field in `src/hub/tool_router.py` (line 38)
- `ToolRegistry.get_policy_requirements()` method retrieves policy from definitions (lines 135-147)
- Pre-defined requirements available: `READ_REPO_REQUIREMENT`, `READ_NODE_REQUIREMENT`, `WRITE_REQUIREMENT`, `LLM_REQUIREMENT`, `NO_POLICY_REQUIREMENT`
- Helper functions: `create_read_requirement()`, `create_write_requirement()`, `create_llm_requirement()`
- DI provider `get_policy_aware_router()` in `src/hub/dependencies.py` (lines 344-361)

**Result**: PASS

---

### 2. Policy Integration Before Execution ✓

**Criterion**: Routing integrates policy checks before execution

**Verification**:
- `PolicyAwareToolRouter.route_tool()` in `src/hub/tool_routing/policy_router.py` (lines 54-131) implements the validation flow:
  1. Check if tool is registered (line 84)
  2. Extract policy requirements from definition (line 90)
  3. Build ValidationContext (lines 102-106)
  4. Run policy validation before handler execution (lines 109-122)
  5. Execute handler only if validation passes (lines 124-131)
- Default fail-closed behavior: returns `READ_NODE_REQUIREMENT` when no explicit policy is set (lines 160-165)
- `_validate_policy()` method (lines 167-218) validates:
  - Node access (lines 186-191)
  - Repo access (lines 194-199)
  - Write target access (lines 202-208)
  - LLM service access (lines 211-216)
- Structured logging at each step with trace_id correlation

**Result**: PASS

---

### 3. MCP-Safe Error Formatting ✓

**Criterion**: Shared error formatting follows the MCP-safe contract

**Verification**:
- `MCPErrorCode` enum in `src/hub/tool_routing/errors.py` (lines 11-38) defines:
  - Standard JSON-RPC 2.0 codes: -32700 to -32603
  - MCP-specific codes: -32000 to -32003
- Error formatting functions:
  - `format_mcp_error()` - base JSON-RPC 2.0 format (lines 55-88)
  - `format_policy_error()` - POLICY_VIOLATION code (lines 91-111)
  - `format_unknown_tool_error()` - UNKNOWN_TOOL code (lines 114-132)
  - `format_validation_error()` - VALIDATION_FAILED code (lines 135-155)
  - `format_access_denied_error()` - ACCESS_DENIED code (lines 158-176)
- Exception classes with `to_mcp_error()` conversion:
  - `ToolExecutionError` (lines 179-218)
  - `PolicyViolationError` (lines 221-240)
  - `ValidationError` (lines 243-260)
- All functions include optional `trace_id` for request correlation

**Result**: PASS

---

## Implementation Files Check

| File | Status | Notes |
|------|--------|-------|
| `src/hub/tool_routing/__init__.py` | ✓ | Package exports all components |
| `src/hub/tool_routing/policy_router.py` | ✓ | PolicyAwareToolRouter with validation |
| `src/hub/tool_routing/requirements.py` | ✓ | PolicyRequirement dataclass and helpers |
| `src/hub/tool_routing/errors.py` | ✓ | MCP error formatting |
| `src/hub/tool_router.py` | ✓ | Policy field added to ToolDefinition |
| `src/hub/dependencies.py` | ✓ | DI provider for PolicyAwareToolRouter |

---

## Code Quality

- Type hints complete across all modules
- Docstrings present for all public classes and methods
- Structured logging with trace_id correlation
- Fail-closed default behavior maintained
- Sensitive parameter redaction in `_sanitize_params()`

---

## Summary

All 3 acceptance criteria verified via code inspection:
1. **Tool registration boundary** - PolicyRequirement defined and integrated with ToolDefinition
2. **Policy integration** - PolicyAwareToolRouter validates before execution with explicit flow
3. **MCP-safe error formatting** - JSON-RPC 2.0 codes with MCP-specific extensions

**QA Result**: PASS ✓

---

## Blocker

None. All acceptance criteria met.

## Closeout Readiness

Ready to close. All artifacts created during implementation are valid and meet the specification.
