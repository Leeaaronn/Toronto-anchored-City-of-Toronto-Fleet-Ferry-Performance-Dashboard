---
status: partial
phase: 01-ingest-profile-dq-baseline
source: [01-VERIFICATION.md]
started: 2026-06-02
updated: 2026-06-02
---

## Current Test

[awaiting human testing]

## Tests

### 1. DQ Report §5 — 5.8% vs ~14% framing
expected: ~14% is attributed to AG 2019.AU2.3; the gap is framed as a period/right-sizing insight (not an error); no claim that 14% was computed from the CSV; the supplied classification is taken as-is, not recomputed.
result: [pending]

### 2. DQ Report §6 + header — pull-date caveat (Assumption A1)
expected: snapshot pull date 2026-06-02 is recorded; the availability dataset is described as "Retired" / point-in-time snapshot; figures are "as of the snapshot"; no imputation claim.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
