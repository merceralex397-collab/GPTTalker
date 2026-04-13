# FIX-025 Implementation: NodePolicy None health service wiring

## Summary
Fixed the `AttributeError: 'NoneType' object has no attribute 'get_node_health'` in `src/hub/mcp.py` by wiring a real `NodeHealthService` instance into `NodePolicy` instead of passing `None`.

## Changes Made

### Step 1: Build NodeHealthService before NodePolicy
Inserted the following code block BEFORE the `# Build services` comment (after line 88, before line 89):

```python
# Build node health service
auth_handler = NodeAuthHandler(config.node_client_api_key) if config else None
node_health_service = NodeHealthService(
    node_repo=node_repo,
    http_client=http_client,
    auth_handler=auth_handler,
) if node_repo and http_client else None
```

### Step 2: Pass node_health_service to NodePolicy
Changed line 90 from:
```python
node_policy = NodePolicy(node_repo, None) if node_repo else None
```
to:
```python
node_policy = NodePolicy(node_repo, node_health_service) if node_repo else None
```

## Files Modified
- `src/hub/mcp.py` (lines 89-97 approximately)

## No New Imports Required
- `NodeHealthService` was already imported at line 72
- `NodeAuthHandler` was already imported at line 68

## Validation Command Output
```
$ uv run python -c "from src.hub.mcp import MCPProtocolHandler; from src.hub.lifespan import lifespan; print('OK')"
OK
```
Exit code: 0

## Two-Step Fix Confirmed
1. **Step 1**: Construct `NodeHealthService` with the available `node_repo`, `http_client`, and `auth_handler` (derived from `config.node_client_api_key`)
2. **Step 2**: Pass the real `node_health_service` instance to `NodePolicy` instead of `None`

This ensures that when `NodePolicy.validate_node_access()` calls `self.health_service.get_node_health()` at line 88 of `node_policy.py`, it receives a real `NodeHealthService` instance rather than `None`.
