# Implementation: FIX-009

## Changes Made

1. **write_target_policy.py**: Added get(target_id) method
2. **markdown.py**: Renamed params (node_id→node, repo_id→write_target, path→relative_path), added mode, added created flag
3. **tools/__init__.py**: Updated schema
4. **node_client.py**: Added mode param
5. **executor.py**: Added mode logic, returns created flag
6. **operations.py**: Added mode to WriteFileRequest

## Acceptance
- mode parameter: PASS
- Parameter names aligned: PASS
- Atomic write preserved: PASS
