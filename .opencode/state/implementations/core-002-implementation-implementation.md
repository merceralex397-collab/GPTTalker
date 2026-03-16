# CORE-002: Implementation Summary - Repo, write-target, and LLM service registries

## Overview

Ticket CORE-002 implements the structured registries for repos, markdown write targets, and LLM service aliases. The database schema, Pydantic models, and repository classes already existed from SETUP-003.

This ticket adds:
- Dependency injection providers to expose repositories to FastAPI endpoints
- Policy validation classes for fail-closed behavior

---

## Files Created

### 1. `src/hub/policy/__init__.py`

Updated to export all policy classes:
- `RepoPolicy` - Repo access validation
- `WriteTargetPolicy` - Write target and extension validation
- `LLMServicePolicy` - LLM service alias validation
- `NodePolicy` (existing)
- `NodeAccessResult` (existing)

### 2. `src/hub/policy/repo_policy.py`

Fail-closed repo access validation with:

| Method | Purpose |
|--------|---------|
| `validate_repo_access(repo_id)` | Validates repo exists, raises ValueError if unknown |
| `validate_path_in_repo(repo_id, file_path)` | Validates file path is within repo bounds |
| `list_accessible_repos()` | Lists all registered repos |
| `list_repos_on_node(node_id)` | Lists repos on a specific node |

### 3. `src/hub/policy/write_target_policy.py`

Write target access and extension allowlist enforcement:

| Method | Purpose |
|--------|---------|
| `validate_write_access(path, extension)` | Validates path exists and extension is allowed |
| `list_write_targets()` | Lists all registered write targets |
| `list_write_targets_for_repo(repo_id)` | Lists write targets for a specific repo |
| `validate_extension(extension, allowed)` | Checks extension against allowlist |

### 4. `src/hub/policy/llm_service_policy.py`

LLM service alias validation with fail-closed behavior:

| Method | Purpose |
|--------|---------|
| `validate_service_access(service_id)` | Validates service exists by ID |
| `validate_service_by_name(name)` | Validates service exists by name |
| `list_services()` | Lists all registered services |
| `list_services_by_type(service_type)` | Lists services filtered by type |
| `get_coding_agent_service()` | Gets configured OpenCode service |
| `get_embedding_service()` | Gets configured embedding service |

---

## Files Modified

### `src/hub/dependencies.py`

Added 6 new DI providers:

**Repository providers:**
- `get_repo_repository(request)` - Returns RepoRepository instance
- `get_write_target_repository(request)` - Returns WriteTargetRepository instance
- `get_llm_service_repository(request)` - Returns LLMServiceRepository instance

**Policy providers:**
- `get_repo_policy(repo_repo)` - Returns RepoPolicy instance
- `get_write_target_policy(write_repo)` - Returns WriteTargetPolicy instance
- `get_llm_service_policy(llm_repo)` - Returns LLMServicePolicy instance

---

## Acceptance Criteria Verification

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Repo registry model exists | ✅ Exists in `src/shared/models.py` (RepoInfo) |
| 2 | Write-target registry model exists | ✅ Exists in `src/shared/models.py` (WriteTargetInfo) |
| 3 | LLM service alias model exists | ✅ Exists in `src/shared/models.py` (LLMServiceInfo) |

---

## Technical Implementation

### Fail-Closed Behavior

All three policy classes enforce fail-closed behavior:
- Unknown repos, write targets, or LLM services raise `ValueError`
- Extension validation rejects disallowed extensions
- All validation attempts are logged with structured logging

### Async/Await

All policy methods are async and use the underlying async repositories.

### Type Hints

Complete type hints on all methods and return types.

### Structured Logging

All policy methods include structured logging with relevant context:
- `repo_access_denied` / `repo_access_granted`
- `write_access_denied` / `write_access_granted`
- `llm_service_access_denied` / `llm_service_access_granted`

---

## Validation

All code passes:
- `ruff check` - No errors
- `ruff format` - All files formatted correctly

---

## Integration Points

These policies will be used by:
- CORE-005 - Policy engine for validation
- CORE-006 - MCP tool routing framework
- REPO-001 - `list_repos` tool
- REPO-002 - `inspect_repo_tree`, `read_repo_file` tools
- WRITE-001 - `write_markdown` tool
- LLM-001 - `chat_llm` tool
- CTX-002 - `index_repo` tool
- XREPO-002 - Cross-repo relationship tracking
