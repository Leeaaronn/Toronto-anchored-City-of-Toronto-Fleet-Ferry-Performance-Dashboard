---
phase: 03-kpi-layer-measures-spec
plan: 01
subsystem: analytics
tags: [duckdb, kpi, sql, parquet, snapshot, fleet, ferry, audit-benchmark]

# Dependency graph
requires:
  - phase: 02-transform-model-join-integrity
    provides: "Gold star schema (fact_vehicle 4,614 w/ 209-NULL AVAILABILITY_YTD + Utilization/specialized_units/role-playing division FKs; fact_ferry 272,529 w/ season/daypart/day_of_week/sales_redemption_gap; dim_division 21) as type-preserving Parquet in data/gold/"
provides:
  - "config.py Phase-3 KPI constants: ASSET_CLASS_TARGETS (95/92/85/88/90), UNIT_TYPE_TO_CLASS, KPI_DIR, KPI_TABLE_CSVS (7), FERRY_COMPLETE_YEARS (2016,2025)"
  - "src/fleet_analytics/kpis.py — DuckDB SQL-first KPI compute module: 8 per-KPI builders, build_scalars, build_all (fail-fast asserts), write_kpi_snapshot, module entrypoint"
  - "Committed falsifiable ground-truth snapshot: data/kpi/kpi_values.json + 7 per-table CSVs"
affects: [03-02-kpi-tests, 03-03-deliverable-docs, 04-powerbi-report-spec]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "KPI compute layer continues the DuckDB SQL-first ingest->transform->model->export module family (one builder per output, build_all orchestrator, fail-fast in-code asserts)"
    - "Audit constants live in config.py and are ?-bound / VALUES-joined into SQL, never inlined"
    - "Scalars -> json.dump (flat, sorted-keys) + table-valued KPIs -> COPY CSV; deterministic snapshot as regression contract"

key-files:
  created:
    - "src/fleet_analytics/kpis.py"
    - "data/kpi/kpi_values.json"
    - "data/kpi/availability_by_class.csv"
    - "data/kpi/availability_by_division.csv"
    - "data/kpi/exception_list.csv"
    - "data/kpi/underutilization_by_division.csv"
    - "data/kpi/ferry_yoy.csv"
    - "data/kpi/ferry_heatmap.csv"
    - "data/kpi/sales_redemption_gap.csv"
  modified:
    - "src/fleet_analytics/config.py"

key-decisions:
  - "Class targets bound via a (VALUES ...) AS ct(unit_type, class_label, target) relation joined on UNIT_TYPE — keeps audit targets out of the SQL string entirely"
  - "Overall availability = single pooled AVG(AVAILABILITY_YTD) over 4,405 non-null rows; mean_of_class_means computed separately ONLY to prove pooled != average-of-averages"
  - "disposal_candidate surfaced as a boolean on exception_list (below class target AND Utilization='Underutilized') — framed as a screening list, never a decision"
  - "Snapshot determinism enforced: secondary ORDER BY tie-breakers on ties + 10-dp round on mean_of_class_means so re-runs produce byte-identical files"

patterns-established:
  - "Deterministic-snapshot rule: every committed-artifact query needs a total-order ORDER BY (tie-breaker column) so the git diff is stable across re-runs"
  - "Gold input read via CREATE OR REPLACE VIEW over read_parquet(config.GOLD_DIR/...) — read-only KPI input that any in-memory con can build over"

requirements-completed: [KPI-01]

# Metrics
duration: 13min
completed: 2026-06-04
---

# Phase 3 Plan 01: KPI Layer Compute & Snapshot Summary

**DuckDB SQL-first kpis.py computing every Domain A (fleet availability/exception/underutilization) and Domain B (ferry YoY/seasonality/heatmap/gap) KPI against audit benchmarks, persisted as a deterministic, git-reviewable ground-truth snapshot (kpi_values.json + 7 CSVs) with pooled-mean / 2020<2019 / max-7229 fail-fast guards.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-06-04T02:19:54Z
- **Completed:** 2026-06-04T02:32:46Z
- **Tasks:** 3
- **Files modified:** 9 created + 1 modified

## Accomplishments
- Added the audit-cited Phase-3 KPI constants to `config.py` (asset-class targets 95/92/85/88/90, UNIT_TYPE->class map, KPI dir/file list, complete-year YoY window) — no threshold ever inlined in SQL.
- Built `kpis.py` mirroring `model.py`: 8 per-KPI builders + `build_scalars` + a `build_all` whose in-code asserts prove the pooled per-vehicle mean is in [0,1] AND differs from the mean-of-class-means, that 2020 ferry Sales < 2019 (COVID dip), and ferry Sales max == 7229.
- Wrote and ran `write_kpi_snapshot`, producing the committed `data/kpi/` snapshot — the falsifiable contract Plan 02 tests and Plan 03 docs consume. Verified deterministic across 3 re-runs and against the full 58-test suite (still green).

## Ground-Truth Values Captured (kpi_values.json)
- overall_availability_rate = **0.8899126467628139** (pooled over 4,405 non-null; 209 NULLs excluded)
- mean_of_class_means = 0.8785521577 (the WRONG grand total, kept to prove pooled != avg-of-avgs)
- availability_by_class gaps (signed actual-target): Light -0.0351, Medium -0.0588, Heavy -0.0552, Off-Road +0.0082, Other +0.0337
- overall_underutilization_rate = **0.05721153846153846** (~5.7%, on 2,080 matched light-duty)
- exception_list = 1,734 below-target units; 34 flagged disposal_candidate
- ferry_sales_max = 7229, ferry_sales_median = 12, lifetime sales/redemptions = 13,257,804 / 13,076,317
- ferry_sales 2019 = 1,249,725 vs 2020 = 366,606 (COVID dip); ferry_yoy rows = complete years 2016..2025 only

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Phase-3 KPI constants to config.py** - `fa7316f` (feat)
2. **Task 2: Build kpis.py compute module (Domain A + B + build_all)** - `bd3b3aa` (feat)
3. **Task 3: Write the committed KPI snapshot (json + 7 CSVs)** - `faeeccc` (feat)

_(write_kpi_snapshot + main() entrypoint were authored alongside the builders in the Task 2 file and finalized/run in Task 3, per the plan's shared-file task split.)_

## Files Created/Modified
- `src/fleet_analytics/config.py` - Added the Phase-3 KPI-layer constants block (targets, UNIT_TYPE map, KPI_DIR, KPI_TABLE_CSVS, FERRY_COMPLETE_YEARS).
- `src/fleet_analytics/kpis.py` - New KPI compute module (load_gold_views, 8 builders, build_scalars, build_all, write_kpi_snapshot, main).
- `data/kpi/kpi_values.json` - Authoritative scalar/benchmark snapshot (flat, sorted keys).
- `data/kpi/{availability_by_class,availability_by_division,exception_list,underutilization_by_division,ferry_yoy,ferry_heatmap,sales_redemption_gap}.csv` - 7 table-valued KPI snapshots.

## Decisions Made
- Class targets are joined in via a `(VALUES ...) AS ct(unit_type, class_label, target)` relation with `?`-bound params rather than a config-driven temp table — keeps the join self-contained per builder and satisfies "no inlined threshold."
- `mean_of_class_means` is computed and stored only to back the canonical "pooled != average-of-averages" guard; it is NOT a reported KPI.
- Snapshot kept under `data/kpi/` (parallel to `data/gold/`) per D-05 discretion — reviewable in git, separate from the Power BI Gold handoff.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] VALUES relation alias shadowed the `ct` join alias**
- **Found during:** Task 2 (build_availability_by_class)
- **Issue:** The class-target relation was aliased `AS class_target(...)` while the SQL referenced `ct.*`, raising `Binder Error: Referenced table "ct" not found`.
- **Fix:** Renamed the relation alias to `ct` in `_class_targets_relation()`.
- **Files modified:** src/fleet_analytics/kpis.py
- **Verification:** `kpis.build_all(con)` runs clean; pooled rate prints 0.8899.
- **Committed in:** bd3b3aa (Task 2 commit)

**2. [Rule 1 - Bug] Non-deterministic snapshot output (ordering + float last-bit)**
- **Found during:** Task 3 (write_kpi_snapshot determinism check)
- **Issue:** Re-running the module changed `underutilization_by_division.csv` (rows tied on rate=0.0 sorted arbitrarily) and `kpi_values.json` (`mean_of_class_means` flipped its last float digit, ...6402 vs ...6401, from DuckDB nested-AVG summation order). The plan requires deterministic regeneration with no diff.
- **Fix:** Added total-order ORDER BY tie-breakers (using_division / owner_division / unit_no / asset_class / season) to every committed-artifact query, and rounded `mean_of_class_means` to 10 dp (far tighter than the ~0.011 pooled-vs-class gap the guard relies on).
- **Files modified:** src/fleet_analytics/kpis.py
- **Verification:** Three consecutive `uv run python -m fleet_analytics.kpis` runs produce byte-identical `data/kpi/` (`diff -r` clean); the pooled-mean guard still passes.
- **Committed in:** faeeccc (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs, Rule 1)
**Impact on plan:** Both fixes were necessary for correctness/determinism of the deliverable. No scope creep — the module signatures, KPI set, and snapshot shape are exactly as planned.

## Issues Encountered
- The worktree had no editable install of `fleet_analytics` (pyproject uses `pythonpath=["src"]` for pytest only). Resolved by invoking ad-hoc scripts and the module with `PYTHONPATH=src uv run ...`; pytest itself already resolves the package via its `pythonpath` setting, so the 58-test suite ran unchanged.
- The `gold` pytest fixture re-wrote `data/gold/*.csv` with CRLF-only churn during the regression run; reverted those out-of-scope files (`git checkout --`) and staged only the intended KPI artifacts.

## Known Stubs
None — every KPI is wired to live Gold data; no placeholder/empty values flow to any output.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The committed snapshot is ready as the regression contract for Plan 02 (`tests/test_kpis.py`) — the pooled-mean grand-total guard, 2020<2019 YoY guard, distribution checks (7229/12), and the 209-NULL exclusion all have concrete snapshot values to assert against.
- The per-KPI builders + `kpi_values.json`/CSVs give Plan 03's `kpi_definitions.md` and `measures_spec.md` exact SQL validation values to pair with each DAX measure.
- No blockers.

## Self-Check: PASSED
- FOUND: src/fleet_analytics/kpis.py, src/fleet_analytics/config.py
- FOUND: data/kpi/kpi_values.json + all 7 per-table CSVs
- FOUND commits: fa7316f, bd3b3aa, faeeccc

---
*Phase: 03-kpi-layer-measures-spec*
*Completed: 2026-06-04*
