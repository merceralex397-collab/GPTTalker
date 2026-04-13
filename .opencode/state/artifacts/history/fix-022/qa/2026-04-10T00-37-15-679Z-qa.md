# QA Verification: FIX-022 — Fix HubNodeClient.read_file HTTP method and endpoint mismatch

## Ticket
- **ID:** FIX-022
- **Stage:** qa
- **Summary:** HubNodeClient.read_file used GET /files/read (wrong endpoint). Changed to POST /operations/read-file with JSON body. Added offset/limit parameters.

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | HubNodeClient.read_file uses POST /operations/read-file with JSON body `{"path": path, "offset": offset, "limit": limit}` | PASS — verified by code inspection |
| 2 | offset and limit parameters passed through correctly | PASS — verified by code inspection |
| 3 | Hub import succeeds | PASS — smoke_test exit code 0 |
| 4 | Node agent import succeeds | PASS — smoke_test exit code 0 |

## Code Inspection Evidence

### File: `src/hub/services/node_client.py`

**Method signature (lines 181-186):**
```python
async def read_file(
    self,
    node: NodeInfo,
    path: str,
    offset: int = 0,
    limit: int | None = None,
) -> dict[str, Any]:
```

**HTTP call (lines 199-204):**
```python
response = await self.post(
    node,
    "/operations/read-file",
    json={"path": path, "offset": offset, "limit": limit},
    timeout=30.0,
)
```

### Verification of Acceptance Criteria

**Criterion 1:** Uses POST /operations/read-file with JSON body
- **Status:** PASS
- **Evidence:** `self.post()` call at line 199 sends request to `/operations/read-file` with `json={"path": path, "offset": offset, "limit": limit}`

**Criterion 2:** offset and limit parameters passed through correctly
- **Status:** PASS
- **Evidence:** Parameters are in signature (lines 185-186) and included in JSON body (line 202)

**Criterion 3:** Hub import succeeds
- **Status:** PASS
- **Evidence:** smoke_test ran successfully — exit code 0

**Criterion 4:** Node agent import succeeds  
- **Status:** PASS
- **Evidence:** smoke_test ran successfully — exit code 0

## Runtime Verification Results

### Command 1: Signature inspection
```
params: ['self', 'node', 'path', 'offset', 'limit']
offset present: True
limit present: True
Exit code: 0
```

### Command 2: Default value verification
```
offset default: 0
limit default: None
Exit code: 0
```

## QA Result

**Overall:** PASS

All 4 acceptance criteria verified. The implementation is correct:
- HTTP method changed from GET to POST
- Endpoint changed from /files/read to /operations/read-file
- JSON body contains path, offset, and limit
- offset defaults to 0
- limit defaults to None

Smoke test passed with both import verification commands exiting 0.