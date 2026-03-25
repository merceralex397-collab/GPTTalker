# Environment Bootstrap

## Ticket

- EXEC-001

## Overall Result

Overall Result: FAIL

## Environment Fingerprint

- fc5f4df429c83f6c0d1731c6438994e10cbb8dcfd008a53776689fe69358c4df

## Missing Prerequisites

- None

## Notes

Bootstrap stopped on the first failing installation command. Inspect the captured output and fix the prerequisite or dependency error before smoke tests.

## Commands

### 1. pip install editable project

- reason: Install project package and declared extras.
- command: `python3 -m pip install -e .`
- exit_code: 1
- duration_ms: 22
- missing_executable: none

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
/usr/bin/python3: No module named pip
~~~~
