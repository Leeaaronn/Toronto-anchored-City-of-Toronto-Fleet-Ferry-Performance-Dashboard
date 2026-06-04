---
phase: 03-kpi-layer-measures-spec
plan: 02
subsystem: analytics
tags: [pytest, kpi, snapshot-as-contract, duckdb, fixture, regression-guard, fleet, ferry]

# Dependency graph
requires:
  - phase: 03-kpi-layer-measures-spec
    plan: 01
    provides: "kpis.build_all(con) compute layer + committed data/kpi snapshot (kpi_values.json + 7 CSVs) as the falsifiable ground-truth contract"
provides:
  - "tests/test_kpis.py — 11 snapshot-as-contract guards (D-06): pooled-mean grand-total (not avg-of-avgs), 209-NULL exclusion (denominator 4,405), 2020<2019 COVID dip, 7229/12 distribution sanity, parametrized by-class gap, snapshot==live, YoY complete-years-only"
  - "Extended gold fixture: kpis.build_all(con) runs once per session so the whole suite asserts over a live KPI layer"
affects: [03-03-deliverable-docs, 04-powerbi-report-spec]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Snapshot-as-contract test layer: committed kpi_values.json / ferry_yoy.csv values asserted == live gold-fixture compute (T-03-04 tampering mitigation)"
    - "Session-scoped gold fixture chain extended one builder at a time (transform -> model -> kpis), mirroring how Phase 2 P02 added model.build_all"
    - "load_gold_views made idempotent: skip Gold names already present as in-memory tables instead of CREATE OR REPLACE VIEW-ing over them"

key-files:
  created:
    - "tests/test_kpis.py"
  modified:
    - "tests/conftest.py"
    - "src/fleet_analytics/kpis.py"

key-decisions:
  - "Float guards compare with round(.,10)/abs(<1e-9) tolerance rather than == on raw doubles — the snapshot already rounds mean_of_class_means to 10 dp and the pooled-vs-class gap is ~0.011, far above tolerance"
  - "test_snapshot_matches_live and test_ferry_yoy_complete_years_only read the committed artifact (kpi_values.json / ferry_yoy.csv) AND the live compute and assert equality — a silently-edited snapshot fails CI (D-06 / threat T-03-04)"
  - "gap_to_target asserted both against the snapshot value and recomputed as rate - target/100 in-test, so the signed-gap rule (D-03) is proven mechanically, not just transcribed"

patterns-established:
  - "When a layer's load_*_views runs over a connection that may already hold those objects (fixture reuse), guard against the DuckDB Table-vs-View CatalogException by skipping names already in information_schema.tables"
  - "Windows CRLF churn on DuckDB COPY-to-CSV regeneration is line-ending-only; revert the out-of-scope data/kpi CSVs with per-file git checkout -- (never blanket reset/clean)"

requirements-completed: [KPI-01]

# Metrics
duration: 9min
completed: 2026-06-04
---

# Phase 3 Plan 02: KPI Test Guards (Snapshot-as-Contract) Summary

**`tests/test_kpis.py` locks the Phase 3 KPI layer with 11 pytest guards that treat the committed `data/kpi` snapshot as the regression contract (D-06) — the canonical pooled-per-vehicle-mean grand total (in [0,1], != mean-of-class-means), the 209-NULL exclusion (denominator 4,405), the 2020<2019 COVID dip, the 7229/12 distribution sanity, the signed by-class gap, and a `snapshot == live compute` assertion that fails CI on any silent snapshot edit.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-06-04
- **Completed:** 2026-06-04
- **Tasks:** 2
- **Files modified:** 1 created + 2 modified

## Accomplishments
- Extended the session-scoped `gold` fixture to run `kpis.build_all(con)` after `model.build_all(con)`, so every test in the suite (and `tests/test_kpis.py` specifically) asserts over a live, in-memory KPI layer — built once per session, no duplicate Bronze ingest.
- Wrote `tests/test_kpis.py` with 11 guards across the 7 required groups: pooled-mean grand-total (in [0,1], ≈0.8899, and proven different from the mean-of-class-means), 209-NULL exclusion (null==209, denominator==4,405), 2020<2019 ferry COVID dip (within the complete-years range), distribution sanity (max==7229, median==12), parametrized by-class rate/target/signed-gap, `snapshot_matches_live` (kpi_values.json headline keys == live compute), and `ferry_yoy_complete_years_only` (year set ⊆ {2016..2025}, snapshot CSV == live).
- Full suite green at **69 passed** (58 prior + 11 new), with the committed `data/gold` and `data/kpi` snapshots left untouched.

## Snapshot Values Locked (the regression contract)
- `overall_availability_rate` = 0.8899126467628139 (pooled over 4,405 non-null; asserted != mean_of_class_means 0.8785521577)
- `availability_null_n` = 209, `availability_nonnull_n` = 4,405 (the 209-NULL exclusion denominator)
- by-class signed gaps: Light −0.0351, Medium −0.0588, Heavy −0.0552, Off-Road +0.0082, Other +0.0337 (each == rate − target/100)
- `ferry_sales_2019` = 1,249,725 vs `ferry_sales_2020` = 366,606 (2020 < 2019, COVID dip)
- `ferry_sales_max` = 7,229, `ferry_sales_median` = 12.0
- ferry_yoy year set = complete years 2016..2025 only

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend the gold fixture so KPIs build once per session** — `ab5b234` (feat) — includes the Rule 3 `load_gold_views` idempotency fix the fixture requires.
2. **Task 2: Write tests/test_kpis.py snapshot-as-contract guards** — `3800775` (test)

## Files Created/Modified
- `tests/test_kpis.py` — 11 KPI snapshot-as-contract guards (183 lines).
- `tests/conftest.py` — `gold` fixture chain extended with `kpis.build_all(con)` (and the `kpis` import added).
- `src/fleet_analytics/kpis.py` — `load_gold_views` made idempotent against an already-populated connection (Rule 3 fix; see Deviations).

## Decisions Made
- Float comparisons use `round(.,10)` / `abs(.) < 1e-9` tolerances rather than raw `==` on doubles — the snapshot already rounds `mean_of_class_means` to 10 dp, and the pooled-vs-class gap (~0.011) is far above tolerance, so the guard is both stable across re-runs and still discriminating.
- The signed by-class gap is asserted twice: against the snapshot value AND recomputed in-test as `rate - target/100`, so D-03 is proven mechanically, not merely transcribed.
- `snapshot_matches_live` and `ferry_yoy_complete_years_only` read the committed artifact (`kpi_values.json` / `ferry_yoy.csv`) via `config.KPI_DIR` and assert it equals the live `gold`-fixture compute — the concrete D-06 / threat-T-03-04 mitigation (a silently-edited snapshot fails CI).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] `load_gold_views` raised a Table-vs-View CatalogException through the fixture**
- **Found during:** Task 1 (running the suite after adding `kpis.build_all(con)` to the `gold` fixture).
- **Issue:** `kpis.build_all(con)` calls `load_gold_views(con)`, which did `CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet(...)` for each Gold table. Through the `gold` fixture those Gold names already exist as **in-memory Tables** (built by `model.build_all(con)`), and DuckDB refuses to replace a Table with a View — `Catalog Error: Existing object dim_division is of type Table, trying to replace with type View`. This cascaded to 34 errors across the suite (every test depending on `gold`). The plan's Task 1 instruction (add `kpis.build_all(con)` to the fixture) could not complete as written without this fix; PATTERNS.md line 81 explicitly anticipated the fixture path reusing the already-built in-memory Gold tables.
- **Fix:** Made `load_gold_views` idempotent — it now queries `information_schema.tables` and skips any Gold name already present, only loading the missing ones from Parquet. This preserves the standalone `main()` path (fresh `:memory:` connection → no existing objects → views created from Parquet, snapshot regeneration unchanged) while letting the fixture reuse the live in-memory Gold tables.
- **Files modified:** `src/fleet_analytics/kpis.py`
- **Verification:** Standalone `uv run python -m fleet_analytics.kpis` still regenerates a content-identical snapshot; full suite 69 passed; `data/gold`/`data/kpi` unchanged.
- **Committed in:** `ab5b234` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking issue, Rule 3). No architectural changes, no scope creep — the fix is the minimal change that lets the planned fixture extension work, and it strengthens the module (the KPI build now composes safely over either a fresh connection or an already-built Gold layer).

## Issues Encountered
- Standalone snapshot regeneration (`python -m fleet_analytics.kpis`) rewrote the 7 `data/kpi/*.csv` with CRLF line endings on Windows (the committed files are LF). A `--ignore-all-space` diff confirmed zero content change (the determinism contract holds); reverted the out-of-scope churn with per-file `git checkout --` (never a blanket reset/clean), per the Plan 01 precedent.
- Ad-hoc `python -c` verification needs `PYTHONPATH=src` because the project uses pytest's `pythonpath=["src"]` (no editable install); pytest itself resolves `fleet_analytics` unchanged.

## Known Stubs
None — every guard asserts against live compute and the committed snapshot; no placeholder/empty values.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- The KPI layer is now proven correct against the committed snapshot: the pooled-mean grand-total, 2020<2019, 7229/12, 209-NULL, and snapshot==live guards are all green, so Plan 03 (`kpi_definitions.md` + `measures_spec.md`) can transcribe `kpi_values.json` / CSV values as SQL validation values with full confidence they are the live truth.
- Phase 4's DAX measures inherit those same SQL validation values; any drift between a future snapshot edit and the live compute now fails CI.
- No blockers.

## Self-Check: PASSED
- FOUND: tests/test_kpis.py, tests/conftest.py
- FOUND commits: ab5b234, 3800775

---
*Phase: 03-kpi-layer-measures-spec*
*Completed: 2026-06-04*
