# REPO-001 Plan Review

## Decision: APPROVED

## Summary

The planning artifact for REPO-001 (list_nodes and list_repos tools) is **approved** with minor observations. The plan correctly addresses all three acceptance criteria, uses existing infrastructure appropriately, and follows the canonical brief conventions.

## Acceptance Criteria Verification

### 1. Nodes list with health metadata is available ✓
- Uses `NodeRepository.list_all()` to get all registered nodes
- Uses `NodeRepository.get_health()` per node to retrieve health metadata
- Returns combined node + health data in the response schema
- Response includes: node_id, name, hostname, status, last_seen, and full health object

### 2. Repo discovery reflects approved registry state only ✓
- Uses `RepoRepository.list_all()` which only returns registered repos
- Uses `RepoRepository.list_by_node()` for filtered queries
- No direct filesystem access - all data comes from the registry

### 3. Unauthorized targets are excluded ✓
- Policy validation runs BEFORE handler execution via PolicyAwareToolRouter
- `list_repos` uses `READ_NODE_REQUIREMENT` to validate node access
- Invalid node_id values are rejected by the policy engine
- MCP error response returned for policy failures

## Integration Verification

All integration points verified against existing code:

| Integration Point | Status |
|---|---|
| `NodeRepository.list_all()` | ✓ Exists at src/shared/repositories/nodes.py:69 |
| `NodeRepository.get_health()` | ✓ Exists at src/shared/repositories/nodes.py:171 |
| `RepoRepository.list_all()` | ✓ Exists at src/shared/repositories/repos.py:83 |
| `RepoRepository.list_by_node()` | ✓ Exists at src/shared/repositories/repos.py:92 |
| `NO_POLICY_REQUIREMENT` | ✓ Exists at src/hub/tool_routing/requirements.py:160 |
| `READ_NODE_REQUIREMENT` | ✓ Exists at src/hub/tool_routing/requirements.py:139 |
| `NodeHealthStatus` enum | ✓ Exists at src/shared/schemas.py:25 |

## Observations

### 1. Policy Consistency (Low severity)
The plan has a minor inconsistency in how `list_nodes` policy is described:
- Line 20 mentions "we use READ_NODE_REQUIREMENT"
- Line 157 uses `NO_POLICY_REQUIREMENT`

The implementation (lines 335+) correctly uses `NO_POLICY_REQUIREMENT`, which is the right choice for a discovery tool that only lists nodes without granting access. This is acceptable because listing nodes doesn't provide any additional access - it just shows what exists.

### 2. Duplicate Code in Plan (Doc质量的 concern)
The plan includes both placeholder handlers (lines 199-214, 269-281) and DI-integrated handlers (lines 352-453). This is confusing for readers but doesn't affect implementation quality since the final implementation will use the DI version.

### 3. Schema Type Usage (Verified)
The plan correctly handles `NodeHealthStatus` enum access:
- `get_health()` returns enum directly (verified at nodes.py:191)
- Plan correctly calls `.value` for serialization

## Risk Assessment

- **Identified risks**: None
- **Assumptions**: Valid (database initialized, registries will have data)
- **Dependencies**: All resolved (CORE-001, CORE-004, CORE-006 are complete)

## Conclusion

The plan is implementation-ready. All acceptance criteria are addressed, integration points are correct, and the approach follows GPTTalker conventions for:
- Pydantic response models
- Structured logging with trace ID
- Policy-integrated tool routing
- FastAPI dependency injection

**Proceed to implementation.**
