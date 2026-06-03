---
phase: 02-transform-model-join-integrity
plan: 03
subsystem: database
tags: [duckdb, parquet, csv, pyarrow, pytest, power-bi, star-schema, data-quality]

# Dependency graph
requires:
  - phase: 02-02
    provides: the five Gold tables (dim_division, fact_vehicle, fact_ferry, dim_date, dim_time) + dq_unmatched_utilization on the gold fixture
  - phase: 02-01
    provides: config.GOLD_DIR / config.GOLD_TABLES constants; TRY_CAST canonical integer key (44 alphanumeric units survive with NULL key)
provides:
  - "export.write_gold(con) — COPY each Gold table to type-preserving Parquet + readable CSV under data/gold/ (10 files)"
  - "MODEL-04 roundtrip gate: AVAILABILITY_YTD DOUBLE+209 NULLs, IN_SERV_DT DATE, BOOLEAN preserved across Parquet and CSV"
  - "data/gold/ Power BI handoff surface (5 .parquet primary + 5 .csv secondary)"
  - "Phase-2 DQ findings addendum: 6-unmatched, 44-alphanumeric, clean 21/20 division reconciliation"
affects: [phase-03-kpis, phase-04-power-bi-report-spec]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Type-preserving Gold export via DuckDB COPY (SELECT * FROM {t}) — no COALESCE/aggregation, NULLs survive the export boundary"
    - "Roundtrip integrity test: second :memory: connection re-reads exported Parquet/CSV in try/finally and asserts typeof + null_ct"
    - "Internal-constant table-name interpolation (GOLD_TABLES) — safe f-string COPY, no external value reaches SQL (T-02-05)"

key-files:
  created:
    - src/fleet_analytics/export.py
    - tests/test_export.py
    - data/gold/ (10 files: 5 .parquet + 5 .csv)
  modified:
    - deliverables/dq_report.md

key-decisions:
  - "Asserted BOOLEAN preservation on dim_date.is_weekend, not fact_vehicle — availability is cross-sectional (no date grain), so fact_vehicle has no boolean column"
  - "data/gold/ committed (not gitignored like data/bronze/) — it is the Power BI handoff deliverable (SHIP-01)"

patterns-established:
  - "Gold export is COPY-only and column-preserving: types and NULLs pass through verbatim to Parquet (primary) + CSV (secondary)"
  - "MODEL-04 roundtrip proves no 0-fill crept in at the export boundary — the integrity control for the locked exclude-never-impute decision"

requirements-completed: [MODEL-04]

# Metrics
duration: 4min
completed: 2026-06-03
---

# Phase 2 Plan 03: Gold Export & DQ Findings Summary

**Type-preserving Gold export (export.write_gold) writing all five star-schema tables to data/gold/ as Parquet + CSV, with a roundtrip test proving AVAILABILITY_YTD survives as DOUBLE with 209 NULLs through both formats (MODEL-04), plus the Phase-2 DQ findings addendum.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-03T05:54Z
- **Completed:** 2026-06-03T05:58:24Z
- **Tasks:** 3
- **Files modified:** 4 (export.py, test_export.py, dq_report.md) + 10 generated Gold artifacts

## Accomplishments
- `export.write_gold(con)` COPYs each of the five Gold tables to `data/gold/{table}.parquet` (FORMAT PARQUET) and `{table}.csv` (FORMAT CSV, HEADER) — 10 files, no COALESCE/aggregation
- MODEL-04 roundtrip gate green: a second `:memory:` reader confirms `fact_vehicle.parquet` keeps `AVAILABILITY_YTD` DOUBLE with exactly **209 NULLs**, `IN_SERV_DT` DATE, and `dim_date.is_weekend` BOOLEAN; `fact_vehicle.csv` re-reads with 209 NULLs (blanks never 0-filled)
- Full suite green: **58 passed** (4 MODEL requirements + all Phase-1 regression guards)
- Documented three Phase-2 DQ findings in `dq_report.md`: the 6 unmatched utilization rows (anti-join, 2,080+6==2,086), the 44 alphanumeric availability units (TRY_CAST NULL-key by design), and the clean 21/20 division-name reconciliation with preserved verbatim truncation

## Task Commits

Each task was committed atomically:

1. **Task 1: export.py — Parquet + CSV COPY for all five Gold tables** - `de48029` (feat)
2. **Task 2: test_export.py — Parquet/CSV roundtrip type + null preservation** - `0d9d8d6` (test)
3. **Task 3: Document 6-unmatched + 44-alphanumeric + division-reconciliation DQ findings** - `afd6f6d` (docs)

_Task 1 (tdd) and Task 2 were committed together as code-then-test: export.py first (de48029), then test_export.py plus the generated Gold files (0d9d8d6). The data/gold/ artifacts ride with the test commit since the test produces and verifies them._

## Files Created/Modified
- `src/fleet_analytics/export.py` - `write_gold(con)`: mkdir GOLD_DIR + COPY each Gold table to Parquet & CSV; type/NULL preserving, internal-constant table names
- `tests/test_export.py` - `test_ten_files_written`, `test_parquet_types`, `test_csv_nulls`: second-:memory: roundtrip asserting 209-null + type preservation
- `data/gold/*.parquet` (5) + `data/gold/*.csv` (5) - the Power BI handoff surface
- `deliverables/dq_report.md` - Phase-2 addendum (§7 6-unmatched, §8 44-alphanumeric, §9 division reconciliation)

## Decisions Made
- **BOOLEAN roundtrip asserted on `dim_date.is_weekend`, not `fact_vehicle`.** The plan's must-have listed `is_weekend as boolean` for `fact_vehicle`, but availability data is cross-sectional (no date grain) — `is_weekend` lives on `dim_date` and `fact_ferry`, never on `fact_vehicle`. The boolean-preservation contract is fully proven via `dim_date.is_weekend` (genuinely BOOLEAN), so the type-fidelity guarantee holds without asserting a non-existent column.
- **`data/gold/` is committed** (only `data/bronze/` is gitignored). These Parquet/CSV files are the SHIP-01 handoff deliverable that Phases 3–4 consume, so they belong in version control.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the BOOLEAN-preservation assertion target**
- **Found during:** Task 2 (test_export.py)
- **Issue:** The plan's must-have and Task 1 behavior note asserted `fact_vehicle.parquet` preserves `is_weekend as boolean`. `fact_vehicle` (model.py:78-95) is `stg_availability.* + utilization fields + division keys` and has no `is_weekend` column — availability is cross-sectional with no date grain. Asserting `typeof(is_weekend)` on `fact_vehicle` would fail with a missing-column error.
- **Fix:** Asserted BOOLEAN preservation on `dim_date.is_weekend` (model.py:140, genuinely BOOLEAN) instead, while keeping the fact_vehicle DOUBLE/DATE/209-null assertions exactly as specified. The boolean-roundtrip contract is satisfied without a phantom column.
- **Files modified:** tests/test_export.py
- **Verification:** `uv run pytest -q tests/test_export.py` → 3 passed; full suite 58 passed
- **Committed in:** `0d9d8d6` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The correction preserves the MODEL-04 type-fidelity intent (DOUBLE + 209 NULLs + DATE + BOOLEAN all proven) without altering any locked numeric target. No scope creep.

## Issues Encountered
None. The `gold` fixture already chained `transform.build_all` + `model.build_all`, so `write_gold` ran directly on it with no fixture changes needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The Gold layer is exported and type-verified: Phase 3 (KPIs) can read `data/gold/*.parquet` directly, and Phase 4 (Power BI report spec) has the type-preserving import surface (almost no Power Query re-typing).
- All four MODEL requirements (MODEL-01..04) are satisfied and locked by tests; Phase 2 is complete.
- DQ narrative for the panel interview is documented (6-unmatched, 44-alphanumeric, clean division reconciliation).

## Self-Check: PASSED
- FOUND: src/fleet_analytics/export.py
- FOUND: tests/test_export.py
- FOUND: data/gold/fact_vehicle.parquet, data/gold/fact_vehicle.csv (and 8 other Gold files)
- FOUND: deliverables/dq_report.md (Phase-2 addendum)
- FOUND commits: de48029, 0d9d8d6, afd6f6d

---
*Phase: 02-transform-model-join-integrity*
*Completed: 2026-06-03*
