---
phase: 02-transform-model-join-integrity
plan: 02
subsystem: database
tags: [duckdb, star-schema, sql, left-join, pytest, parquet-ready]

# Dependency graph
requires:
  - phase: 02-transform-model-join-integrity (Plan 01)
    provides: stg_availability / stg_utilization / stg_ferry staging tables with unit_key_int, fleet_age, ferry derived fields; gold fixture scaffold; config.GOLD_EXPECTED_ROWS
provides:
  - "model.py: five Gold tables (dim_division, fact_vehicle, fact_ferry, dim_date, dim_time) + dq_unmatched_utilization, built via model.build_all(con)"
  - "Flagship availability⋈utilization LEFT JOIN (fact_vehicle, 4,614 rows, no fan-out) with role-playing owner/using division FKs"
  - "MODEL-03 join-integrity hard gate + MODEL-02 dimension tests (8 tests, < 1s)"
  - "dq_unmatched_utilization (6 rows) for the Plan-03 DQ finding"
affects: [03-kpis-measures, kpi-aggregation, parquet-export, power-bi-handoff, dq-report]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gold builders mirror ingest.py/transform.py: one private CREATE OR REPLACE TABLE per table + build_all(con) with fail-fast count loop"
    - "Conformed dimension via normalized distinct union + ROW_NUMBER surrogate; role-playing FKs resolved by joining normalized name back to the dim"

key-files:
  created:
    - src/fleet_analytics/model.py
    - tests/test_join_integrity.py
    - tests/test_dimensions.py
  modified:
    - tests/conftest.py

key-decisions:
  - "fact_vehicle is availability-anchored (LEFT JOIN on unit_key_int); 44 alphanumeric units (NULL key) survive — never INNER JOIN, never pre-filter the key"
  - "Role-playing division FKs (owner_division_key always populated, using_division_key NULL for non-light-duty) resolved by joining the SAME normalized name expression used to build dim_division"
  - "6 unmatched utilization rows surfaced only via the dq_unmatched_utilization anti-join (outside the availability-anchored fact by design); 2080 + 6 == 2086"
  - "dim_date uses a natural DATE date_key (Power BI 'Mark as Date Table'); dim_division/dim_time use integer ROW_NUMBER surrogates"
  - "No COALESCE/fillna on AVAILABILITY_YTD — 209 NULLs flow through the join into fact_vehicle"

patterns-established:
  - "Shared _NORM normalization expression reused for both dim_division build and FK resolution so names reconcile exactly (no spelling force-maps, D-06)"
  - "In-code fail-fast Gold count loop against config.GOLD_EXPECTED_ROWS so regressions fail in model.build_all, not only in pytest"

requirements-completed: [MODEL-02, MODEL-03]

# Metrics
duration: 4min
completed: 2026-06-03
---

# Phase 2 Plan 02: Gold Star-Schema Build & Join Integrity Summary

**Five Gold tables in `model.py` — the conformed `dim_division` (21), the availability-anchored `fact_vehicle` (4,614) with the flagship availability⋈utilization LEFT JOIN and role-playing division FKs, `fact_ferry` (272,529), gapless `dim_date` (4,383) and 96-row `dim_time` — all guarded by the MODEL-03 join-integrity hard gate and MODEL-02 dimension tests.**

## Performance

- **Duration:** ~4 min
- **Tasks:** 2
- **Files modified:** 4 (1 created module, 2 created tests, 1 modified fixture)

## Accomplishments
- `model.build_all(con)` builds the full Gold layer in dependency order (dim_division before fact_vehicle so the FK joins resolve) with a fail-fast count loop against `config.GOLD_EXPECTED_ROWS`.
- Flagship `fact_vehicle`: availability-anchored LEFT JOIN, exactly 4,614 rows with no fan-out (unique `UNIT_NO`), 2,080 rows carrying a non-null Utilization, two role-playing division FKs, and the 209 AVAILABILITY_YTD NULLs preserved through the join.
- `dq_unmatched_utilization` anti-join captures the 6 unmatched utilization rows (2,080 + 6 == 2,086) for the Plan-03 DQ finding.
- Conformed `dim_division` (21 rows, unique surrogate key), gapless `dim_date` (4,383, span == count), `dim_time` (96).
- 8 new tests green; full suite 55 passed.

## Task Commits

1. **Task 1: Create model.py — five Gold tables + the flagship join** - `e931fc0` (feat) [TDD: RED via tests committed in Task 2's files; GREEN = this implementation]
2. **Task 2: Wire gold fixture + test_join_integrity.py + test_dimensions.py** - `7e7d18d` (test)

_TDD note: the RED tests (test_join_integrity.py / test_dimensions.py) and the fixture wiring were authored and confirmed failing (ImportError: no `model`) before model.py existed; they belong to the Task-2 file set per the plan's task→file map, so they are committed under Task 2. GREEN was confirmed before the Task-1 commit._

**Plan metadata:** (final docs commit follows this summary)

## Files Created/Modified
- `src/fleet_analytics/model.py` - Five Gold-table builders + `dq_unmatched_utilization` anti-join + `build_all(con)` with fail-fast count loop.
- `tests/test_join_integrity.py` - MODEL-03 hard gate: matched 2080 / unmatched 6 (recon 2086) / fact 4614 / unique key / util key non-null.
- `tests/test_dimensions.py` - MODEL-02: dim_date gapless 4383, dim_time 96, dim_division conformed 21.
- `tests/conftest.py` - `gold` fixture now calls `model.build_all(con)` after `transform.build_all(con)`.

## Decisions Made
None beyond the locked Phase-2 decisions (D-01..D-06) the plan encodes. The role-playing FK resolution reuses a single shared `_NORM` normalization expression (module-level) for both the `dim_division` build and the `owner_division_key`/`using_division_key` joins, guaranteeing names reconcile exactly without spelling force-maps (D-06).

## Deviations from Plan

None - plan executed exactly as written. The verified RESEARCH SQL bodies (Examples 2, 5, 6) hit their target counts on first run; no auto-fixes (Rules 1-3) were needed.

## Issues Encountered
- A bare `python -c` invocation could not resolve the `fleet_analytics` package (src layout not on path); re-ran verification with `sys.path.insert(0,'src')`. No code impact — pytest (which configures the src path) was the authoritative gate. Confirmed: fact_vehicle 209 nulls, owner_division_key 0 nulls, using_division_key never populated when Utilization is NULL.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Gold star schema is built and tested; ready for Plan 03 (KPI/measures + DQ findings + Parquet export).
- `dq_unmatched_utilization` (6 rows) is materialized and ready to feed the Plan-03 DQ finding.
- fact_ferry remains at full 15-minute grain; any KPI rollup is a Phase-3 concern per RESEARCH Open Question 2.

---
*Phase: 02-transform-model-join-integrity*
*Completed: 2026-06-03*
