# Smoke Test

## Ticket

- FIX-022

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `uv run python -c import inspect; from src.hub.services.node_client import HubNodeClient; m=HubNodeClient.read_file; lines=inspect.getsourcelines(m)[0]; code="".join(lines); checks=["/operations/read-file" in code, "data.get(\"success\")" in code, "data.get(\"data\"," in code]; print("checks:", checks); assert all(checks), f"FAIL: {checks}"; print("PASS")`
- exit_code: 0
- duration_ms: 1709
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
checks: [True, True, True]
PASS
~~~~

#### stderr

~~~~text
<no output>
~~~~
