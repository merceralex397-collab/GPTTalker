# Implementation of FIX-012: Complete cross-repo landscape with real metrics

## Summary

Implemented FIX-012: "Complete cross-repo landscape with real metrics". Replaced hardcoded zeros with real queries.

## Changes Made

### 1. src/shared/repositories/issues.py
- Added `count_by_repo(repo_id)` method to count issues per repository

### 2. src/hub/services/qdrant_client.py
- Added `count_files_by_repo(repo_id)` - counts indexed files using Qdrant scroll API
- Added `get_unique_languages(repo_id)` - extracts unique languages from file payloads

### 3. src/hub/services/cross_repo_service.py
- Updated constructor to accept `issue_repo` parameter
- Updated `search_across_repos()` - replaced hardcoded file_count=0 and issue_count=0 with real queries
- Updated `get_project_landscape()` - replaced hardcoded values with real queries

### 4. src/hub/dependencies.py
- Added IssueRepository dependency to `get_cross_repo_service()`

## Acceptance Criteria

- ✅ file_count reflects actual indexed file count from Qdrant
- ✅ issue_count reflects actual issue count from IssueRepository
- ✅ languages are detected from indexed file extensions
- ✅ Relationship finder already uses content hash overlap (no changes needed)

All queries include error handling with graceful fallback to 0 or empty list on failure.