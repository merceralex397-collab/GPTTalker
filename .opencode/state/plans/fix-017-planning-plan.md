# Implementation Plan for FIX-017: Clean up duplicate endpoints, response models, and artifact registry

## Summary

This plan addresses three cleanup items:
1. Duplicate `/health` endpoint in hub (main.py has it, should be in routes.py)
2. Health endpoint returns raw dict instead of HealthResponse Pydantic model
3. Duplicate SETUP-002 artifact in registry.json and inconsistent `kind` field values

## Scope

### Files to Modify
- `src/hub/main.py` - Remove duplicate `/health` endpoint
- `src/hub/routes.py` - Add proper `/health` endpoint with HealthResponse model
- `.opencode/state/artifacts/registry.json` - Remove duplicate SETUP-002 entry and standardize kind values

### Files to Review
- `src/hub/routes.py` - Verify HealthResponse model definition

## Implementation Steps

### Step 1: Remove duplicate /health endpoint from main.py
- Delete lines 67-88 in `src/hub/main.py` (the `@app.get("/health")` endpoint)
- The endpoint should only exist in routes.py

### Step 2: Add /health endpoint to routes.py with HealthResponse
- The HealthResponse model already exists at lines 36-42 in routes.py
- Add a new `/health` endpoint in routes.py that uses the HealthResponse model
- The endpoint should:
  - Check database connectivity using `check_database_health` dependency
  - Return a HealthResponse instance with proper fields

### Step 3: Verify HealthResponse model
- Current HealthResponse in routes.py (lines 36-42):
  ```python
  class HealthResponse(BaseModel):
      status: str
      service: str
      database: dict[str, Any] | None = None
  ```
- This model is suitable for the hub's /health endpoint
- No changes needed to the model itself

### Step 4: Fix duplicate SETUP-002 artifact in registry.json
- In `.opencode/state/artifacts/registry.json`:
  - Keep the entry at lines 36-42 (first SETUP-002 with `kind: "plan"`)
  - Remove the duplicate at lines 44-50 (second SETUP-002 with `kind: "planning"`)
- Both entries are for the planning stage, so the duplicate should be removed

### Step 5: Standardize kind field values
- Review all artifact kind values in registry.json
- Standardize to these canonical kinds:
  - `planning` - for planning stage artifacts
  - `implementation` - for implementation summaries
  - `review` - for code review artifacts
  - `qa` - for QA verification
  - `smoke-test` - for deterministic smoke tests
  - `backlog-verification` - for process verification
- Change any "plan" to "planning" for consistency

## Validation Plan

1. **Syntax validation**: Run `python3 -m py_compile src/hub/main.py src/hub/routes.py` to verify no syntax errors
2. **Import validation**: Run `python3 -c "from src.hub.main import app; from src.hub.routes import router"` to verify imports work
3. **Registry validation**: Verify JSON is valid and no duplicate ticket/stage/kind combinations exist
4. **Health endpoint test**: Verify the /health endpoint returns proper HealthResponse format

## Risks and Assumptions

- **Risk**: Moving /health from main.py to routes.py could break existing health check integrations
  - **Mitigation**: The endpoint path remains the same (/health), just the implementation location changes
- **Risk**: Registry.json modification could cause artifact tracking issues
  - **Mitigation**: Only removing a true duplicate, not changing actual artifact files
- **Assumption**: The HealthResponse model in routes.py is the canonical model for the hub
- **Assumption**: No other code depends on main.py's health_check implementation details

## Acceptance Criteria Verification

| Criterion | Verification |
|-----------|---------------|
| Single /health endpoint in routes.py | Verify only routes.py defines /health |
| Health endpoint returns HealthResponse | Check response_model=HealthResponse is set |
| No duplicate artifact entries | Run JSON validation and check for duplicates |
| Consistent kind field values | Audit all kind values for consistency |
