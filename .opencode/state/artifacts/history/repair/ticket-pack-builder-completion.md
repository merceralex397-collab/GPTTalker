---
- completed_stage: ticket-pack-builder
- cycle_id: 2026-04-07T22:18:12Z
- completed_by: scafforge-repair
- summary: Created REMED-001 (EXEC001 hub import NameError) and REMED-002 (REF-003 advisory). Manifest updated.
- evidence:
  - tickets/REMED-001.md
  - tickets/REMED-002.md
  - tickets/manifest.json
  - diagnosis/20260407-221355/manifest.json
---

## ticket-pack-builder Completion

Remediation tickets created for post-repair source-layer findings:

- **REMED-001**: EXEC001 — `src/hub/dependencies.py` uses `RelationshipService` (imported under `TYPE_CHECKING`) as a runtime return-type annotation. Fix: use string annotation to defer resolution. Hub cannot import until fixed.
- **REMED-002**: REF-003 (advisory) — `.opencode/node_modules/zod/src/index.ts` missing-module false positive. npm dependency tree, not a project import issue.

Diagnosis basis: `diagnosis/20260407-221355`
