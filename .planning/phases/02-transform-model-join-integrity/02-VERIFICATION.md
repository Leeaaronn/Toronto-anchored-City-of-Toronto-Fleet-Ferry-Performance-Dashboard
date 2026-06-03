---
phase: 02-transform-model-join-integrity
verified: 2026-06-03T00:00:00Z
status: passed
score: 12/12 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 2: Transform, Model & Join Integrity — Verification Report

**Phase Goal:** The Gold star schema exists as type-preserving Parquet with the value-added availability⋈utilization join correct and tested — the critical-path node that the disposal-candidate cross-measure, ferry heatmap, and time-intelligence all depend on.
**Verified:** 2026-06-03
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria + PLAN frontmatter)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | UNIT_NO normalized to canonical integer on both datasets; 44 alphanumeric availability units survive with NULL key (TRY_CAST) | VERIFIED | Live query: `stg_availability` NULL key count == 44; `stg_utilization` NULL key count == 0; `fact_vehicle` row count == 4,614 (no rows dropped). `transform.py` uses `TRY_CAST(UNIT_NO AS BIGINT)` not plain `CAST`. |
| 2 | Ferry timestamps rounded to 15-min slots; 0 NaT, 272,529 rows preserved | VERIFIED | Live query: `stg_ferry` COUNT == 272,529; NULL ts_15 count == 0. `test_ferry_ts15` passes. |
| 3 | All six derived fields produced: fleet_age, season, daypart, day_of_week, is_weekend, sales_redemption_gap | VERIFIED | All six columns confirmed present on `stg_ferry` (via `information_schema`). `fleet_age` and `unit_key_int` confirmed on `stg_availability`. `test_derived_fields.py` — 23 tests green. |
| 4 | fact_vehicle == 4,614 rows, no fan-out, unique UNIT_NO key | VERIFIED | Live query: COUNT(*) == 4,614; COUNT(DISTINCT UNIT_NO) == 4,614. `model.build_all` fail-fast loop confirms; `test_fact_rowcount_4614` and `test_fact_unique_key` pass. |
| 5 | Matched (Utilization IS NOT NULL) == 2,080; unmatched == 6; 2,080 + 6 == 2,086 | VERIFIED | Live queries: matched == 2,080; `dq_unmatched_utilization` COUNT == 6; 2,080+6 == 2,086. `test_matched_2080` and `test_unmatched_6` pass. |
| 6 | 6 unmatched utilization rows documented as a DQ finding | VERIFIED | `deliverables/dq_report.md` section §7 documents the 6 unmatched rows with anti-join rationale and reconciliation. `grep 'unmatched'` confirmed. |
| 7 | dim_division == 21 conformed rows with unique surrogate keys | VERIFIED | Live query: COUNT(*) == 21; COUNT(DISTINCT division_key) == 21. `test_dim_division_conformed` passes. |
| 8 | dim_date gapless 2015-01-01 to 2026-12-31, == 4,383 rows; dim_time == 96 rows | VERIFIED | Live query: COUNT == 4,383; datediff span == 4,383 (gapless). `dim_time` COUNT == 96. `test_dim_date_gapless` and `test_dim_time_96` pass. |
| 9 | AVAILABILITY_YTD 209 NULLs preserved through the join into fact_vehicle (no imputation) | VERIFIED | Live query: `COUNT(*) - COUNT(AVAILABILITY_YTD)` on `fact_vehicle` == 209. No COALESCE/fillna in live SQL in `transform.py` (occurrences in docstrings only). `test_availability_nulls_preserved` passes. |
| 10 | fact_vehicle carries owner_division_key (always populated) and using_division_key (nullable for non-light-duty) | VERIFIED | Live query: `owner_division_key IS NULL` count == 0 (always populated). `using_division_key IS NOT NULL` where `Utilization IS NULL` count == 0 (correctly NULL for non-matched rows). Columns confirmed in `fact_vehicle` column list. |
| 11 | All five Gold tables exported as type-preserving Parquet + readable CSV (10 files); 209 NULLs and DATE/DOUBLE/BOOLEAN types preserved | VERIFIED | `data/gold/` confirmed: 5 .parquet + 5 .csv files. `test_parquet_types`: AVAILABILITY_YTD == DOUBLE with 209 NULLs; IN_SERV_DT == DATE; `dim_date.is_weekend` == BOOLEAN. `test_csv_nulls`: re-read NULL count == 209. All three export tests pass. |
| 12 | REFERENCE_YEAR=2023 documented in config.py (D-08); dim_division 44-alphanumeric-unit and division-reconciliation DQ findings in dq_report.md | VERIFIED | `config.REFERENCE_YEAR == 2023` with inline citation comment. `dq_report.md` §8 documents 44 alphanumeric units; §9 documents clean 21/20 reconciliation with ENVIRONMENT,CLIMATE&FORESTR truncation note. |

**Score: 12/12 truths verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/fleet_analytics/config.py` | REFERENCE_YEAR=2023, GOLD_DIR, GOLD_TABLES, GOLD_EXPECTED_ROWS | VERIFIED | All four constants present and correct. GOLD_EXPECTED_ROWS maps all 5 tables. REFERENCE_YEAR=2023 with rationale comment. |
| `src/fleet_analytics/transform.py` | build_all(con) + 3 private builders; TRY_CAST key; all 6 derived fields; no COALESCE | VERIFIED | 100 lines, substantive. build_keyed_availability, build_keyed_utilization, build_staged_ferry all present. TRY_CAST confirmed. No COALESCE/fillna in live SQL. |
| `src/fleet_analytics/model.py` | 5 Gold table builders + build_all + fail-fast count loop | VERIFIED | 194 lines, substantive. All 6 builders (dim_division, fact_vehicle, dq_unmatched_utilization, fact_ferry, dim_date, dim_time) present. Fail-fast loop at lines 186-191 against GOLD_EXPECTED_ROWS. |
| `src/fleet_analytics/export.py` | write_gold(con) — COPY to Parquet + CSV | VERIFIED | 47 lines, substantive. COPY loop with FORMAT PARQUET and FORMAT CSV, HEADER. Uses internal config.GOLD_TABLES only. |
| `tests/conftest.py` | gold fixture calling transform.build_all + model.build_all | VERIFIED | gold fixture at line 23 calls `transform.build_all(con)` then `model.build_all(con)`. Session-scoped. |
| `tests/test_derived_fields.py` | Parametrized MODEL-01 derived-field tests | VERIFIED | 124 lines. test_ferry_ts15, test_key_normalization, test_availability_nulls_preserved, test_fleet_age (3 cases), test_season (7 cases), test_season_daypart (9 cases), test_gap_signed. 23 tests green. |
| `tests/test_join_integrity.py` | MODEL-03 hard gate: matched/unmatched/fan-out/unique-key | VERIFIED | 64 lines. test_matched_2080, test_unmatched_6, test_fact_rowcount_4614, test_fact_unique_key, test_util_key_not_null. 5 tests green. |
| `tests/test_dimensions.py` | MODEL-02: dim_date gapless, dim_time 96, dim_division conformed | VERIFIED | 40 lines. test_dim_date_gapless (span==count assert), test_dim_time_96, test_dim_division_conformed. 3 tests green. |
| `tests/test_export.py` | MODEL-04 roundtrip: Parquet type/null + CSV null preservation | VERIFIED | 101 lines. test_ten_files_written, test_parquet_types (DOUBLE+209 NULLs+DATE+BOOLEAN), test_csv_nulls (209 NULLs). 3 tests green. Second :memory: reader pattern. |
| `data/gold/` (10 files) | 5 .parquet + 5 .csv for all Gold tables | VERIFIED | All 10 files present: dim_date, dim_division, dim_time, fact_ferry, fact_vehicle in both formats. |
| `deliverables/dq_report.md` | Phase-2 addendum with 6-unmatched + 44-alphanumeric + division-reconciliation findings | VERIFIED | Sections §7, §8, §9 document all three Phase-2 findings with counts, rationale, and test references. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `transform.py` | `config.REFERENCE_YEAR` | `?` binding in fleet_age SELECT | VERIFIED | Line 48: `[config.REFERENCE_YEAR]` param; `(? - YEAR) AS fleet_age` in SQL |
| `conftest.py gold fixture` | `transform.build_all` | fixture body call | VERIFIED | Line 33: `transform.build_all(con)` |
| `conftest.py gold fixture` | `model.build_all` | fixture body call after transform | VERIFIED | Line 34: `model.build_all(con)` |
| `model.py fact_vehicle` | `stg_availability LEFT JOIN stg_utilization` | ON unit_key_int | VERIFIED | Line 89: `LEFT JOIN stg_utilization u ON a.unit_key_int = u.unit_key_int` |
| `model.py fact_vehicle FKs` | `dim_division.division_key` | normalized-name join | VERIFIED | Lines 91-94: two LEFT JOINs to dim_division using shared `_NORM` expression |
| `export.py write_gold` | `config.GOLD_DIR / config.GOLD_TABLES` | COPY FORMAT PARQUET / CSV | VERIFIED | Lines 44-46: `COPY (SELECT * FROM {t}) TO '{p}.parquet' (FORMAT PARQUET)` and CSV equivalent |
| `test_export.py` | `data/gold/fact_vehicle.parquet + .csv` | second :memory: con re-reads exported files | VERIFIED | Lines 57-98: `read_parquet` and `read_csv` on the exported files in a separate `:memory:` connection |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `fact_vehicle` (AVAILABILITY_YTD) | AVAILABILITY_YTD | Bronze availability CSV → stg_availability → LEFT JOIN | Yes — DuckDB DOUBLE with 209 genuine NULLs, confirmed live | FLOWING |
| `fact_vehicle` (Utilization) | Utilization | stg_utilization LEFT JOIN | Yes — 2,080 non-null / 2,534 NULL (non-matched) | FLOWING |
| `fact_ferry` | ts_15, season, daypart, etc. | stg_ferry (time_bucket + CASE transforms of Bronze ferry data) | Yes — 272,529 rows, all derived fields populated, 131,329 negative gaps | FLOWING |
| `dim_date` (is_weekend) | is_weekend BOOLEAN | generate_series 2015-01-01→2026-12-31 | Yes — BOOLEAN type confirmed via typeof() on parquet roundtrip | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full pytest suite green | `uv run pytest -q` | 58 passed in 2.13s | PASS |
| Locked Gold counts all match | Live DuckDB queries against built tables | All 5 tables exact: 21/4614/272529/4383/96 | PASS |
| Join integrity: matched==2080, unmatched==6, reconcile 2086 | Live queries | matched=2080, unmatched=6, sum=2086 | PASS |
| 209 NULLs through join | `COUNT(*) - COUNT(AVAILABILITY_YTD) FROM fact_vehicle` | 209 | PASS |
| 44 alphanumeric units survive with NULL key | NULL key count on stg_availability | 44 | PASS |
| No fan-out | COUNT(*) == COUNT(DISTINCT UNIT_NO) on fact_vehicle | 4614 == 4614 | PASS |
| owner_division_key always populated | NULL count | 0 | PASS |
| dim_date gapless | datediff span == COUNT | 4383 == 4383 | PASS |
| Parquet type fidelity | typeof(AVAILABILITY_YTD) on roundtrip | DOUBLE; 209 NULLs; DATE; BOOLEAN | PASS |
| CSV null preservation | NULL count on CSV re-read | 209 | PASS |
| Signed sales_redemption_gap (no abs) | Negative gap count | 131,329 rows with negative gap | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| MODEL-01 | 02-01-PLAN.md | UNIT_NO canonical key; ferry 15-min slots; 6 derived fields | SATISFIED | All 6 derived fields confirmed on staging tables; TRY_CAST verified; 23 tests green |
| MODEL-02 | 02-02-PLAN.md | Gold star-schema: dim_division, fact_vehicle, fact_ferry, dim_date, dim_time | SATISFIED | All 5 tables built at exact counts; 3 dimension tests green |
| MODEL-03 | 02-02-PLAN.md | Availability⋈utilization join integrity: matched=2080, unmatched=6, no fan-out, unique key | SATISFIED | All 5 join-integrity tests green; anti-join table materialized; DQ finding documented |
| MODEL-04 | 02-03-PLAN.md | All 5 Gold tables as type-preserving Parquet + CSV; 209 NULLs preserved | SATISFIED | 10 files in data/gold/; 3 export tests green; Parquet DOUBLE/DATE/BOOLEAN roundtrip proven |

**All 4 requirements satisfied. No orphaned requirements.**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_derived_fields.py` | 82-85 | `test_fleet_age` executes `SELECT ? - ?` against synthetic values, not `stg_availability.fleet_age` column | WARNING (WR-01 from code review) | Tautological test: does not guard against a wrong expression in `transform.py`. Mitigated by `test_gap_signed` which does assert against the actual column. `test_key_normalization` and `test_availability_nulls_preserved` are also real column assertions. |
| `tests/test_derived_fields.py` | 94-97, 107-110 | `test_season` and `test_season_daypart` re-run the CASE SQL on synthetic literals via `_SEASON_SQL`/`_DAYPART_SQL`, not the actual `stg_ferry.season`/`daypart` columns | WARNING (WR-01) | Same tautology risk as above. However, the production SQL in `transform.py` and the `_SEASON_SQL`/_DAYPART_SQL` in the test are visually identical, so a change to the wrong one is unlikely. The gap_signed test and key_normalization test are genuine column guards. |
| `tests/test_export.py` | 42-45, 55, 88 | `export.write_gold(gold)` writes to tracked `data/gold/` directory with no temp_path redirect | WARNING (WR-02 from code review) | Each pytest run overwrites committed Gold files. Acceptable because data/gold/ is intentionally a committed deliverable (SHIP-01), but introduces test-side-effect coupling to repo state. |
| `tests/test_derived_fields.py` | 72 | `import pytest` placed mid-module with `# noqa: E402` | INFO (IN-01) | Cosmetic; no functional impact. |
| `tests/conftest.py` | 15, 23 | `-> duckdb.DuckDBPyConnection` return annotation on yield-based fixtures | INFO (IN-02) | Type annotation mismatch; harmless at runtime. |

**No BLOCKER-tier anti-patterns. No TBD/FIXME/XXX debt markers in modified files.**

WR-01 tautological test observation (from code review): The `test_fleet_age`, `test_season`, and `test_season_daypart` tests duplicate the transform SQL logic into `_SEASON_SQL`/`_DAYPART_SQL` constants and evaluate them against synthetic literals. They do not query the produced columns on `stg_availability` or `stg_ferry` and therefore cannot catch a divergence between the test SQL and the actual production SQL. This is a test-quality gap, not a pipeline correctness failure — the production pipeline was independently verified by live queries above. `test_gap_signed` is the correct pattern (queries the actual column) and serves as the strongest MODEL-01 column guard. The code review (02-REVIEW.md, WR-01) documents the recommended fix.

---

### Human Verification Required

None. All must-haves are verifiable programmatically and have been confirmed via live code execution.

---

## Gaps Summary

No blocking gaps found. The phase goal is fully achieved:

1. The Gold star schema builds at all locked counts (21/4614/272529/4383/96).
2. The value-added availability⋈utilization join is correct: matched=2,080, unmatched=6, 2,080+6=2,086, no fan-out, unique key, owner_division_key always populated.
3. All six MODEL-01 derived fields are present and live on the produced tables.
4. All 10 Gold export files exist in data/gold/ with Parquet type fidelity and 209-null preservation proven by roundtrip test.
5. Three Phase-2 DQ findings are documented in deliverables/dq_report.md.
6. All 58 tests pass (58/58) in 2.13s.

The three WARNING-level findings from the code review (WR-01 tautological derived-field tests, WR-02 export tests write to tracked directory, WR-03 unescaped path in COPY) are test-layer quality issues. They do not affect pipeline correctness or phase goal achievement. They are carried forward as improvement items for Phase 3 test authoring.

---

_Verified: 2026-06-03_
_Verifier: Claude (gsd-verifier)_
