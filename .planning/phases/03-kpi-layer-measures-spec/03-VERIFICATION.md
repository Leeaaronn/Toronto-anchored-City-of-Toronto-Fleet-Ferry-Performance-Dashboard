---
phase: 03-kpi-layer-measures-spec
verified: 2026-06-04T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 3: KPI Layer & Measures Spec — Verification Report

**Phase Goal:** Every KPI has an authoritative SQL/Python ground-truth value cross-checked against audit benchmarks, paired with copy-paste DAX in a measures spec — the values the Power BI dashboard must reproduce.
**Verified:** 2026-06-04
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All Domain A KPIs computed: pooled availability rate, by-class vs target + gap, exception list, underutilization overall/by-division, specialized split, disposal-candidate cross-measure | VERIFIED | `kpis.py` builders (`build_availability_by_class`, `build_availability_by_division`, `build_exception_list`, `build_underutilization_by_division`) + committed CSVs confirmed. `exception_list.csv` = 1,734 rows, 34 `disposal_candidate=true`. `availability_by_class.csv` has all 5 classes. |
| 2 | All Domain B ferry KPIs computed: lifetime/period totals, YoY with 2020 < 2019 asserted, seasonality, DoW × hour heatmap, sales-to-redemption gap; max ≈ 7,229 / median ≈ 12 | VERIFIED | `build_ferry_yoy`, `build_ferry_seasonality`, `build_ferry_heatmap`, `build_sales_redemption_gap` all present. `ferry_yoy.csv` years = 2016-2025 only. `ferry_heatmap.csv` = 168 rows (7 DoW × 24 hours). `ferry_sales_max == 7229`, `ferry_sales_median == 12.0` confirmed by live test. |
| 3 | Overall availability is the pooled per-vehicle mean (NOT mean-of-class-means), all rates in [0,1], asserted by test as canonical grand-total guard | VERIFIED | `test_pooled_grand_total_mean` passes: pooled = 0.8899126467628139, mean-of-class-means = 0.8785521577, diff = 0.011360 > 1e-9. Both the in-code `build_all` assert and the pytest guard confirm this. |
| 4 | KPI definitions doc (formulas) and DAX-ready measures spec pair each KPI with copy-paste DAX + SQL validation value, including the 5.8% vs 14% reconciliation note | VERIFIED | `deliverables/kpi_definitions.md` and `deliverables/measures_spec.md` confirmed to exist and contain all required elements. All SQL validation values cross-checked verbatim against `kpi_values.json` and per-table CSVs — zero drift found. |

**Score:** 4/4 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fleet_analytics/kpis.py` | DuckDB SQL-first KPI compute: 8 builders + `build_scalars` + `build_all` + `write_kpi_snapshot` | VERIFIED | 490 lines. All builders present. `build_all` contains 4 fail-fast asserts (pooled in [0,1]; pooled != mean-of-class; 2020<2019; max==7229). Module entrypoint present (`main()`). |
| `src/fleet_analytics/config.py` | `ASSET_CLASS_TARGETS`, `UNIT_TYPE_TO_CLASS`, `KPI_DIR`, `KPI_TABLE_CSVS` (7 names), `FERRY_COMPLETE_YEARS` | VERIFIED | All constants present and correct: targets 95/92/85/88/90, 5 UNIT_TYPE keys, `FERRY_COMPLETE_YEARS = (2016, 2025)`, 7-name CSV list. |
| `data/kpi/kpi_values.json` | Scalar snapshot with `overall_availability_rate`, `availability_nonnull_n`, `availability_null_n`, `ferry_sales_max`, by-class entries, 2019/2020 ferry sales | VERIFIED | File exists, valid JSON, all required keys present. Values confirmed: rate=0.8899126467628139, nonnull=4405, null=209, max=7229, 2019=1249725, 2020=366606, median=12.0. |
| `data/kpi/ferry_yoy.csv` | Per-complete-year ferry totals 2016-2025 only | VERIFIED | 10 rows, years {2016..2025}, no 2015/2026. 2020 sales (366,606) < 2019 sales (1,249,725) confirmed. |
| `data/kpi/availability_by_class.csv` | 5 rows, one per asset class, with rate/target/gap columns | VERIFIED | 5 rows, all 5 classes present, all rates in [0,1]. |
| `data/kpi/availability_by_division.csv` | 21 rows (one per owner division) | VERIFIED | 21 rows, all rates in [0,1]. |
| `data/kpi/exception_list.csv` | Below-target units with `disposal_candidate` boolean | VERIFIED | 1,734 rows, `disposal_candidate` column present, 34 = true. |
| `data/kpi/underutilization_by_division.csv` | Per using-division underutilization rate | VERIFIED | Present, includes `specialized_share` column. |
| `data/kpi/ferry_heatmap.csv` | 168 rows (7 DoW × 24 hours) | VERIFIED | 168 rows confirmed, columns: `day_of_week`, `hour_of_day`, `sales`, `redemptions`, `slots_n`. All 24 hours and 7 days present. |
| `data/kpi/sales_redemption_gap.csv` | Per-complete-year signed sales-redemption gap | VERIFIED | 10 rows (2016-2025), `total_gap` column with signed values. 2016 = +92,649, 2020 = -7,940 match measures_spec.md citations exactly. |
| `tests/test_kpis.py` | 11 snapshot-as-contract guards | VERIFIED | 11 tests, all PASS confirmed by live run. |
| `tests/conftest.py` | `gold` fixture extended with `kpis.build_all(con)` | VERIFIED | `kpis.build_all(con)` present in fixture chain at line 37, after `model.build_all(con)`. |
| `deliverables/kpi_definitions.md` | Plain-language formulas, audit benchmarks, 5.8%/14% reconciliation, AG-theme traceability, Sources footer | VERIFIED | All required elements confirmed: `14%`, `AU2.2`, `AU2.3`, "screening" + "SME", `4,405`, "Reconciliation", Sources & Licence footer. |
| `deliverables/measures_spec.md` | Domain A/B sections, `Measure name | DAX | SQL validation value | Notes` tables, Sources footer | VERIFIED | All required elements confirmed: `SQL validation value`, `DIVIDE`, Fleet Maintenance + Ferry sections, `7,229`, `0.8899`, `13,257,804`, `NOT AVERAGEX`, `COUNTROWS non-null`, scope-split note, Sources & Licence footer. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `kpis.py` | `config.ASSET_CLASS_TARGETS` | `_class_targets_relation()` builds `(VALUES ?, ?, ?) AS ct(...)` | WIRED | Confirmed: targets are `?`-bound from config into every by-class SQL. No threshold value inlined in SQL strings. |
| `kpis.py` | `data/gold/*.parquet` | `load_gold_views` via `read_parquet(config.GOLD_DIR / t + '.parquet')` | WIRED | `load_gold_views` iterates `config.GOLD_TABLES`, idempotent against in-memory tables. `build_all` calls it first. |
| `kpis.py` | `data/kpi/kpi_values.json` | `json.dump(build_scalars(con), ...)` in `write_kpi_snapshot` | WIRED | `write_kpi_snapshot` confirmed to call `build_scalars(con)` and `json.dump` to the `KPI_DIR / "kpi_values.json"` path. |
| `tests/test_kpis.py` | `tests/conftest.py` `gold` fixture | `def test_*(gold)` signature | WIRED | Every test function accepts the `gold` fixture parameter. `gold` fixture chain: `con` → `ingest_bronze` → `transform.build_all` → `model.build_all` → `kpis.build_all`. |
| `tests/test_kpis.py` | `data/kpi/kpi_values.json` | `json.load(config.KPI_DIR / "kpi_values.json")` in `test_snapshot_matches_live` | WIRED | `test_snapshot_matches_live` loads the committed JSON and asserts live compute == persisted values for `overall_availability_rate`, `availability_null_n`, `ferry_sales_max`. |
| `deliverables/measures_spec.md` | `data/kpi/kpi_values.json` | SQL validation value cells transcribed verbatim | WIRED | Every SQL validation value cross-checked programmatically — zero drift between doc figures and snapshot for all 12 headline metrics checked. |
| `deliverables/kpi_definitions.md` | `deliverables/dq_report.md` | "extends and cross-references the existing reconciliation table at dq_report.md §5" | WIRED | §A-Reconciliation explicitly cross-references `dq_report.md §5`; "14%" present. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `kpis.py` / `availability_by_class` | `AVG(AVAILABILITY_YTD)` | `fact_vehicle` Gold Parquet via `read_parquet` | Yes — DuckDB GROUP BY SQL, live aggregate | FLOWING |
| `kpis.py` / `build_scalars` | `overall_availability_rate` | `AVG(AVAILABILITY_YTD) FROM fact_vehicle` on live Gold data | Yes — direct query result 0.8899126467628139 | FLOWING |
| `kpis.py` / `ferry_yoy` | `SUM("Sales Count")` by year | `fact_ferry` Gold Parquet, filtered to 2016-2025 | Yes — live aggregate, COVID dip confirmed | FLOWING |
| `kpis.py` / `build_ferry_heatmap` | `SUM("Sales Count")` by DoW × hour | All `fact_ferry` rows | Yes — 168-row grid, all cells populated | FLOWING |
| `tests/test_kpis.py` | All guard values | Live `gold` fixture compute + committed JSON | Yes — test assertions compare live compute to snapshot; `test_snapshot_matches_live` explicitly cross-references | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command / Check | Result | Status |
|----------|----------------|--------|--------|
| `uv run pytest tests/test_kpis.py -q` | 11 KPI guards | 11 passed in 0.76s | PASS |
| `uv run pytest -q` (full suite) | All 69 tests | 69 passed in 2.23s | PASS |
| Pooled availability in [0,1] and != mean-of-class-means | Live `build_all` asserts | 0.8899 != 0.8786, diff=0.011360 | PASS |
| `ferry_yoy.csv` contains only 2016-2025 | CSV year set check | {2016..2025}, no 2015/2026 | PASS |
| `exception_list.csv` row count and `disposal_candidate` | CSV parse | 1,734 rows, 34 `disposal_candidate=true` | PASS |
| All doc values match `kpi_values.json` | Programmatic cross-check | All 12 headline metrics match, 5 by-class entries match | PASS |
| `sales_redemption_gap.csv` spot values | CSV parse | 2016=+92,649, 2020=-7,940 (match doc) | PASS |
| No COALESCE/fill on `AVAILABILITY_YTD` in kpis.py | Code scan | COALESCE appears only in a prohibition comment; no SQL usage | PASS |
| No raw threshold values inlined in SQL | Code scan | No `/ 95`, `< 0.95`, etc. in SQL strings | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| KPI-01 | 03-01, 03-02 | All Domain A/B KPIs computed authoritatively in SQL/Python, cross-checked against audit benchmarks | SATISFIED | All 8 builders present and tested. 69 tests pass. In-code fail-fast asserts run clean. |
| KPI-02 | 03-03 | KPI definitions doc + DAX-ready measures spec pairing each KPI with copy-paste DAX + SQL validation value | SATISFIED | Both deliverable docs confirmed substantive, no drift vs snapshot. |

**Note:** `REQUIREMENTS.md` shows KPI-01 as `[ ]` (Pending) at line 26 — this is a tracking-doc update gap; the implementation is fully satisfied per the codebase evidence above. KPI-02 is correctly marked `[x]`. The status row in the traceability table (line 78) also shows KPI-01 as "Pending". This does not affect phase-goal achievement — it is an unflushed status update in a planning doc.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `deliverables/kpi_definitions.md` | 109 | References `data/kpi/ferry_seasonality` (no `.csv` extension; file does not exist on disk) | WARNING | The `ferry_seasonality` builder runs in-memory (`build_ferry_seasonality`) and the KPI is computed correctly, but the output is not committed as a CSV. The docs reference it as a location for detail. Phase 4's report spec referencing this file will find nothing on disk. |
| `deliverables/measures_spec.md` | 71 | References `data/kpi/ferry_seasonality` for the B3 SQL validation value | WARNING | Same root cause as above — the seasonality profile is computable but not materialized as a committed file. |

No BLOCKER anti-patterns found. No `TBD`, `FIXME`, or `XXX` markers in any modified file.

---

### Gaps Summary

No BLOCKER gaps. One WARNING requiring awareness:

**ferry_seasonality CSV not committed.** The `build_ferry_seasonality` function in `kpis.py` runs correctly (verified by full test suite passing and in-code asserts), but `ferry_seasonality` is not in `config.KPI_TABLE_CSVS` and therefore not exported by `write_kpi_snapshot`. Both `kpi_definitions.md` and `measures_spec.md` reference `data/kpi/ferry_seasonality` as where the seasonality profile lives — that file does not exist on disk. The plan's `files_modified` list never included `ferry_seasonality.csv` (7 CSVs were the deliberate committed set), so this was an intentional design choice, but the doc references are broken. Phase 4 can tolerate this because the heatmap CSV (`ferry_heatmap.csv`) is committed and covers the DoW×hour demand story; the seasonality profile would add month-level detail. This is a documentation reference inconsistency, not a data-fidelity or KPI-correctness issue.

---

### Human Verification Required

None — all phase-3 deliverables are code, data files, and Markdown documents. No UI, real-time behavior, or external service integration is involved. All observable truths are mechanically verifiable and have been verified.

---

## Final Assessment

**Status: PASSED**

All four roadmap success criteria are met:

1. Every Domain A KPI is computed in SQL/Python with the correct 209-NULL exclusion (denominator 4,405), audit-cited thresholds bound via `?`-params (never inlined), and all rates in [0,1].
2. Every Domain B ferry KPI is computed; the COVID dip (2020 < 2019) is a locked test guard; distribution stats (max 7,229 / median 12) are asserted; the YoY table contains only complete years 2016-2025.
3. Overall availability is the pooled per-vehicle mean (0.8899), proven different from the mean-of-class-means (0.8786) by both in-code asserts and the `test_pooled_grand_total_mean` guard — the canonical "not average-of-averages" proof.
4. `kpi_definitions.md` and `measures_spec.md` are substantive deliverable docs with verbatim-transcribed snapshot values, copy-paste DAX, the 5.8%-vs-14% reconciliation, AG-theme traceability (AU2.2/AU2.3), SME-screening framing for the disposal-candidate list, and a Sources & Licence footer. Zero drift found between any cited figure and the committed snapshot.

The test suite (69 tests, 11 KPI-specific) passes in full. No blocker anti-patterns, no imputation of the 209 NULLs, no hardcoded thresholds in SQL. Phase 4 can proceed with `measures_spec.md` as the DAX build contract.

---

*Verified: 2026-06-04*
*Verifier: Claude (gsd-verifier)*
