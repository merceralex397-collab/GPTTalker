# Backlog Verification — FIX-005

## Ticket
- **ID:** FIX-005
- **Title:** Fix structured logger TypeError and HubConfig attribute error
- **Stage:** closeout
- **Status:** done
- **Verification state:** PASS

## Verification Summary
Two bugs fixed:
1. **StructuredLogger TypeError:** Logger calls with extra kwargs (`logger.info(..., key=value)`) no longer raise TypeError — JSON handler accepts arbitrary keyword args
2. **HubConfig AttributeError:** `config.database_path` replaced with `config.database_url` in hub lifespan

## Evidence
1. **Structured logging verification:** All structured logging calls with extra fields (tool_name, trace_id, node, etc.) work without TypeError
2. **HubConfig verification:** `HubConfig` uses `database_url` consistently; lifespan references correct attribute
3. **Log output:** Structured log output includes all required fields (tool_name, trace_id, duration_ms, outcome)

## Acceptance Criteria Status
| Criterion | Status |
|---|---|
| Structured logging calls with extra kwargs do not raise TypeError | PASS |
| Hub startup completes without AttributeError on database_path | PASS |
| Log output includes structured fields (tool_name, trace_id, etc.) | PASS |

## Notes
- Standard Python Logger raises TypeError on unexpected keyword arguments — JSON handler overrides `info()`/`error()` etc. to absorb extras
- The fix aligns with structured logging requirements in the canonical brief
- No follow-up ticket needed
