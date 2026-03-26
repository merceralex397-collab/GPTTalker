# Implementation: EXEC-007 — Restore discovery and inspection contract behavior in hub tools

## Summary

Implemented three targeted bug fixes in src/hub/tools/discovery.py and src/hub/tools/inspection.py to restore contract-tested behavior.

## Changes Made

### Bug 1: list_nodes_impl string vs enum handling (discovery.py)

Added _get_status_value() and _get_health_status_value() helper functions to handle both string and enum types.

### Bug 2: inspect_repo_tree_handler validation order (inspection.py)

Added empty node_id and repo_id validation before dependency checks.

### Bug 3: read_repo_file_handler validation order (inspection.py)

Added empty file_path validation before dependency checks.

## Validation Results

Ruff lint: All checks passed
Import check: PASS  
Contract tests: 3 passed, 29 deselected
