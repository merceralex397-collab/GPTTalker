# Code Review: CORE-006 — MCP tool routing framework

**Review Type:** Fix Verification  
**Date:** 2026-03-16  
**Status:** APPROVED  

## Fix Verification Summary

The implementer's fix for the policy behavior issue has been **verified and confirmed correct**.

### Issue Addressed

**Previous behavior (incorrect):** The `_get_policy_requirement()` method returned `None` when no explicit policy was set, causing validation to be skipped for tools without explicit policy requirements.

**Fixed behavior (correct):** Now returns `READ_NODE_REQUIREMENT` as the default, enforcing basic node validation for all tools without explicit policy declarations.

### Verification Details

| Check | Status | Evidence |
|-------|--------|----------|
| Fix applied to code | ✅ | `policy_router.py` lines 160-165 return `READ_NODE_REQUIREMENT` |
| Default enforces validation | ✅ | `READ_NODE_REQUIREMENT` has `requires_node=True` |
| Fail-closed maintained | ✅ | Comments on lines 145-149 and 160-162 explicitly document fail-closed intent |
| Explicit opt-out preserved | ✅ | Legacy `requires_policy_check=False` still returns `None` (lines 154-158) |
| Import exists | ✅ | `READ_NODE_REQUIREMENT` imported from `requirements.py` (line 163) |

### Code Changes Verified

```python
# Default: require basic node validation for fail-closed behavior
# Unknown tools without explicit policy must go through basic validation
# This maintains the security posture from CORE-005
from src.hub.tool_routing.requirements import READ_NODE_REQUIREMENT

return READ_NODE_REQUIREMENT
```

### Acceptance Criteria Confirmation

1. **Tool registration boundary is defined** ✅ — Tool definitions now include optional `policy` field
2. **Routing integrates policy checks before execution** ✅ — All tools now undergo node validation by default
3. **Shared error formatting follows the MCP-safe contract** ✅ — JSON-RPC 2.0 error codes used consistently

### Integration Confirmation

- Dependencies: SETUP-004 (transport), CORE-002 (registries), CORE-005 (policy engine) — all integrated correctly
- Type safety: Complete type hints on all methods
- Documentation: Docstrings updated to reflect fail-closed default behavior

### Observations

No remaining issues. The fix correctly addresses the medium-severity finding from the previous review.

---

**Approval Signal:** This ticket is ready to advance to QA stage.
