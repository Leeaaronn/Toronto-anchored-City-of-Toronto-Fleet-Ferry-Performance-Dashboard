---
phase: 02-transform-model-join-integrity
plan: 01
subsystem: transform
tags: [duckdb, staging, key-normalization, derived-fields, tdd, model-01]
requires:
  - "Phase 1 Bronze tables (bronze_availability/utilization/ferry) on a session con"
  - "Phase 1 con fixture (in-memory DuckDB, Bronze ingested once)"
provides:
  - "transform.build_all(con) -> stg_availability / stg_utilization / stg_ferry"
  - "Canonical integer join key (unit_key_int) on both vehicle datasets"
  - "Six derived fields: fleet_age, season, daypart, day_of_week, is_weekend, sales_redemption_gap"
  - "config Gold constants: REFERENCE_YEAR, GOLD_DIR, GOLD_TABLES, GOLD_EXPECTED_ROWS"
  - "gold pytest fixture (extends once with model.build_all in Plan 02)"
affects:
  - "Plan 02 model.build_all consumes stg_* tables + extends the gold fixture"
  - "Plan 02 fact_vehicle LEFT JOIN keys on unit_key_int"
tech-stack:
  added: []
  patterns:
    - "TRY_CAST(UNIT_NO AS BIGINT) canonical key (never plain CAST)"
    - "Single CREATE OR REPLACE TABLE AS SELECT per builder, mirroring ingest.py"
    - "Scalar month()/hour()/isodow()/dayname() over double-quoted date_part"
    - "TDD RED/GREEN with session-scoped gold fixture"
key-files:
  created:
    - "src/fleet_analytics/transform.py"
    - "tests/test_derived_fields.py"
  modified:
    - "src/fleet_analytics/config.py"
    - "tests/conftest.py"
decisions:
  - "REFERENCE_YEAR=2023 anchored to the May-2023 FSD report / audit 2022-2023 benchmarks (D-08)"
  - "fleet_age left signed: negatives (future model years 2024-2026) are legitimate, not clamped"
  - "gold fixture calls only transform.build_all this plan; one model.build_all line added in Plan 02"
metrics:
  duration: ~3 min
  completed: 2026-06-03
---

# Phase 2 Plan 01: Transform / Keyed + Derived Staging Layer Summary

Built the Phase-2 staging layer (MODEL-01): canonical-integer `UNIT_NO` key on both
vehicle datasets via `TRY_CAST`, ferry 15-minute slotting, and all six derived fields,
gated by a new `gold` fixture and `test_derived_fields.py` — 47 tests green on DuckDB 1.5.3.

## What Was Built

- **`config.py` (Task 1):** `REFERENCE_YEAR=2023` (documented D-08 rationale), `GOLD_DIR`,
  `GOLD_TABLES`, and `GOLD_EXPECTED_ROWS` added without touching any Bronze constant.
- **`transform.py` (Task 2, TDD):** three private builders
  (`build_keyed_availability`, `build_keyed_utilization`, `build_staged_ferry`) plus
  `build_all(con)`. `stg_availability` exposes `unit_key_int` (44 alnum units survive with
  NULL key) and `fleet_age = REFERENCE_YEAR - YEAR` (bound `?`, negatives kept).
  `stg_utilization` exposes `unit_key_int` (0 NULL keys). `stg_ferry` exposes `ts_15`,
  `season`, `daypart`, `day_of_week`, `is_weekend`, and signed `sales_redemption_gap`.
  No COALESCE/fillna — the 209 AVAILABILITY_YTD NULLs flow through.
- **`conftest.py` + `test_derived_fields.py` (Task 3):** session-scoped `gold` fixture
  calling `transform.build_all`; parametrized boundary tests for season/daypart/fleet_age,
  ferry 15-min preservation, key normalization, null preservation, and signed-gap.

## Verification

- `uv run pytest -q tests/test_derived_fields.py` -> 23 passed.
- `uv run pytest -q` (full suite) -> 47 passed (Phase-1 209/4,405 null guards intact).
- Pattern scan: no `COALESCE`/`fillna`/non-TRY `CAST(UNIT_NO AS BIGINT)`/double-quoted
  `date_part(` in `transform.py` (all hits are `TRY_CAST` or docstring references).
- Live invariants confirmed by tests: stg_availability 4614 rows / 44 NULL keys / 209
  AVAILABILITY_YTD NULLs; stg_utilization 0 NULL keys; stg_ferry 272529 rows / 0 NaT ts_15.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Parameter-count mismatch in test SQL (self-authored)**
- **Found during:** Task 2 GREEN run (after transform.py passed, 9 daypart cases failed).
- **Issue:** `_DAYPART_SQL` contains 6 `hour(?::TIMESTAMP)` placeholders (and `_SEASON_SQL` 3),
  but the parametrized tests bound only 4 / 3 values, raising `InvalidInputException: Values
  were not provided for prepared statement parameters 5, 6`.
- **Fix:** Bind `[ts] * SQL.count("?")` so the literal timestamp is supplied for every
  placeholder regardless of how many times the scalar appears in the CASE expression.
- **Files modified:** `tests/test_derived_fields.py`
- **Commit:** 88c4c57

This was a defect in the test scaffolding I wrote (Task 3), not in the production transform —
`transform.py` itself passed unchanged once the test binding was corrected. The transform
SQL was never the source of failure.

## Authentication Gates

None — local read-only CSV -> in-memory DuckDB; no auth surface.

## Known Stubs

None. All six derived fields and both keys are wired against real Bronze data; no
placeholder/empty values introduced.

## TDD Gate Compliance

RED (ef7051a, `test(...)`) -> GREEN (40e9809, `feat(...)`) gate sequence satisfied. The
RED run failed on the missing `transform` import (not a passing-by-accident test), then GREEN
turned the suite green. A follow-up `fix(...)` (88c4c57) corrected a test-only binding bug.

## Commits

- 6eb013d `feat(02-01)`: Gold-layer constants in config.py (Task 1)
- ef7051a `test(02-01)`: failing MODEL-01 tests + gold fixture (Task 3 RED)
- 40e9809 `feat(02-01)`: transform staging layer (Task 2 GREEN)
- 88c4c57 `fix(02-01)`: bind one timestamp per ? in test SQL (Rule 1)

## Self-Check: PASSED

- FOUND: src/fleet_analytics/transform.py
- FOUND: tests/test_derived_fields.py
- FOUND: src/fleet_analytics/config.py (REFERENCE_YEAR present)
- FOUND: tests/conftest.py (gold fixture present)
- FOUND commits: 6eb013d, ef7051a, 40e9809, 88c4c57
