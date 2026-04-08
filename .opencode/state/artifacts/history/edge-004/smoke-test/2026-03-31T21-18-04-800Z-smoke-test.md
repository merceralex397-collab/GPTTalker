# Smoke Test

## Ticket

- EDGE-004

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `python3 -c import json; m=json.load(open('tickets/manifest.json')); e1=next(t for t in m['tickets'] if t['id']=='EDGE-001'); e2=next(t for t in m['tickets'] if t['id']=='EDGE-002'); assert e1['resolution_state']=='superseded', 'EDGE-001 not superseded'; assert e2['resolution_state']=='superseded', 'EDGE-002 not superseded'; print('EDGE-001 resolution_state:', e1['resolution_state']); print('EDGE-002 resolution_state:', e2['resolution_state']); print('SMOKE TEST PASS')`
- exit_code: 0
- duration_ms: 20
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
EDGE-001 resolution_state: superseded
EDGE-002 resolution_state: superseded
SMOKE TEST PASS
~~~~

#### stderr

~~~~text
<no output>
~~~~
