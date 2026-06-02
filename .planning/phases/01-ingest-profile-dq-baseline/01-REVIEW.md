---
phase: 01-ingest-profile-dq-baseline
reviewed: 2026-06-02T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - src/fleet_analytics/config.py
  - src/fleet_analytics/ingest.py
  - src/fleet_analytics/profile.py
  - src/fleet_analytics/schemas.py
  - src/fleet_analytics/__init__.py
  - tests/conftest.py
  - tests/test_nulls.py
  - tests/test_profile.py
  - tests/test_rowcounts.py
  - tests/test_schemas.py
  - pyproject.toml
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-06-02
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

This phase ingests three City of Toronto CSVs into typed DuckDB Bronze tables, computes deterministic DQ facts, and enforces Pandera contracts under pytest. I ran the pipeline and the full suite (23 passed in ~1.3s) and independently re-derived every headline figure against the live source CSVs — all match (209 nulls / 4,405 non-null, 120 underutilized of 2,086, 21/19 distinct domains, year 1982–2026, ferry sales median 12 / max 7,229, redemption median 11 / max 7,216, availability strictly in [0,1]).

The data-fidelity rules are correctly honoured: `AVAILABILITY_YTD` is typed `DOUBLE` (blanks → SQL NULL, never imputed, never COALESCE'd), `UNIT_NO` stays `VARCHAR` (zero-padding preserved), `Utilization` is value-set-guarded rather than recomputed, and the ~14% audit benchmark is cited not recalculated. I also confirmed a robustness property the code relies on implicitly: DuckDB `read_csv` raises `BinderException` if a `types` key names a missing column, so a re-supplied CSV with a renamed load-bearing column fails loudly at ingest rather than silently re-inferring its type.

**No Critical issues found.** The findings below are correctness-masking patterns, a stack-pin deviation from the mandated `CLAUDE.md` stack, dead computed output, and test-design brittleness. None blocks the phase, but the WARNING items should be addressed before Phase 2 builds on this output.

## Warnings

### WR-01: `int()` truncation of DuckDB `median()` silently masks a half-step / wrong median

**File:** `src/fleet_analytics/profile.py:109-112`
**Issue:** `ferry_sales_median` and `ferry_redemption_median` are produced as `int(ferry_sales_median)` / `int(ferry_redemption_median)`. DuckDB `median()` over a `BIGINT` column with an even row count returns the *average of the two middle values*, i.e. a `.5` float is possible. `int()` truncates toward zero, so a true median of `12.5` would be reported as `12`. On the current 272,529-row data the medians happen to land on whole numbers (12, 11), so the tests pass — but the cast bakes in a silent rounding error that will misreport the "median 12 vs max 7,229" skew story if the data is re-supplied with an even count whose middle straddles two values. The DQ report transcribes these numbers as authoritative, so the defect is invisible until the figure is wrong.
**Fix:** Keep the float and round explicitly only at the reporting boundary, or assert the value is integral before casting:
```python
ferry_sales_median_raw = q('SELECT median("Sales Count") FROM bronze_ferry').fetchone()[0]
# either report the float as-is, or:
assert ferry_sales_median_raw == int(ferry_sales_median_raw), (
    f"median is non-integral ({ferry_sales_median_raw}); int() would truncate"
)
ferry_sales_median = int(ferry_sales_median_raw)
```

### WR-02: DuckDB pin (`>=1.4,<1.5`) contradicts the mandated stack (DuckDB 1.5.x)

**File:** `pyproject.toml:6`
**Issue:** `CLAUDE.md` (Technology Stack + Version Compatibility) explicitly mandates **DuckDB 1.5.x** ("DuckDB (Python client) 1.5.x", "DuckDB 1.5.0 (Mar 2026)", "Commit `uv.lock`"). The project pins `duckdb>=1.4,<1.5`, which *excludes* 1.5.x entirely. For a deliverable whose value proposition is a "reproducible, defensible, audit-grounded" pipeline, shipping a stack that diverges from the documented/cited stack is a defensibility gap a panel could flag. It is not a correctness bug on current data, but it undermines the reproducibility claim and the cited "Sources" rationale.
**Fix:** Align the pin with the mandate, e.g. `"duckdb>=1.5,<1.6"`, re-run the suite to confirm green, and commit the updated `uv.lock`. If 1.4 was a deliberate compatibility choice, document the deviation in `CLAUDE.md`/phase notes so it is defensible rather than silent.

### WR-03: `test_no_null_became_zero` does not actually test what its name/docstring claims

**File:** `tests/test_nulls.py:37-47`
**Issue:** The docstring asserts this test guards against "any accidental fill that would inflate non_null toward 4,614" and "null → zero" conversion. It only re-checks the same three counts (`total/non_null/null_ct`) already verified by `test_null_count` and `test_nonnull_count`. It therefore detects a fill *only if the fill changes the COUNT* (e.g. `COALESCE` of NULL→0 raises non-null). A fill that replaces NULLs with another **non-null** value (e.g. mean-imputation to `0.92`) produces the identical count split and passes — yet that is exactly the "never impute" violation the locked decision forbids. The test name oversells its coverage and could give false confidence that imputation is structurally blocked.
**Fix:** Either rename to reflect the real guarantee (count reconciliation) or add a guard that catches value-level imputation, e.g. assert the distribution of NULLs is preserved by counting rows where the column `IS NULL` directly rather than only the aggregate, and/or assert the non-null count exactly equals the count of rows that were non-blank in the source:
```python
def test_null_count_is_structural_not_imputed(con):
    # IS NULL count must match the gap, independent of COUNT(col) arithmetic
    explicit_null = con.execute(
        "SELECT COUNT(*) FROM bronze_availability WHERE AVAILABILITY_YTD IS NULL"
    ).fetchone()[0]
    assert explicit_null == 209
```

### WR-04: Profiling tests are coupled to a hand-authored markdown deliverable (brittle / false-red risk)

**File:** `tests/test_profile.py:67-73`
**Issue:** `test_dq_report_artifact_exists` is in the *unit* profiling test module but asserts the existence of `deliverables/dq_report.md` and greps it for the literal string `"5.8%"`. This couples the code-correctness suite to a manually maintained narrative artifact: the test goes red if the deliverable is moved/renamed, if someone writes "5.8 %" or "5.8&nbsp;%", or in any checkout where deliverables are not present (CI matrix, partial clone). It does not validate that the *computed* rate equals 5.8% (that is `test_underutilized_rate`); it only string-matches prose. This conflates "is the pipeline correct" with "is the report written," weakening the suite's signal.
**Fix:** Move artifact-existence checks into a dedicated `test_deliverables.py` (or mark with a `deliverables` marker that CI can select), and derive the asserted figure from `profile_facts` rather than a hard-coded literal so the report and the code cannot silently diverge:
```python
rate_str = f"{round(profile_facts(con)['underutilized_rate'] * 100, 1)}%"
assert rate_str in report.read_text(encoding="utf-8")
```

## Info

### IN-01: `distinct_status_desc` is computed but never asserted (dead output)

**File:** `src/fleet_analytics/profile.py:90-92, 118`
**Issue:** `distinct_status_desc` is queried and returned in the facts dict but no test in `test_profile.py` asserts it (unlike `distinct_owner_division`/`distinct_category_class`, which are guarded). It is therefore an unguarded, effectively dead figure — if a CSV re-supply changes the STATUS_DESC domain (currently 4), nothing fails. Either drop it or add a regression assertion.
**Fix:** Add `assert facts["distinct_status_desc"] == 4` to `test_distinct_domains`, or remove the unused computation.

### IN-02: `availability_null_pct` is computed and returned but never asserted

**File:** `src/fleet_analytics/profile.py:106`
**Issue:** `availability_null_pct` (0.0453) is emitted but no test pins it, while the deliverable transcribes "4.53%". Like IN-01, it is an unguarded figure the report depends on.
**Fix:** Add `assert facts["availability_null_pct"] == 0.0453` (or compute the expected from counts) to `test_availability_nulls`.

### IN-03: Table names are interpolated into SQL via f-strings

**File:** `src/fleet_analytics/profile.py:35,54,61,65,71,73,86,etc.`; `src/fleet_analytics/ingest.py:45,71`; `tests/*`
**Issue:** Every `con.execute(f"... {table} ...")` interpolates an identifier into SQL. All values are hard-coded module constants / fixed tuples, so this is **not** exploitable here. Flagged only as a pattern: if any of these helpers later accepts a caller-supplied table name, it becomes an injection vector. The CSV *path* is correctly parameterized (`?`), but identifiers cannot be parameterized in SQL, so this is acceptable as-is given the constant inputs.
**Fix:** No action required now. If `_summarize`/`_create_bronze` ever take external input, validate the identifier against an allowlist before interpolation.

### IN-04: Per-CSV ingest is hard-wired to three calls; `EXPECTED_ROWS`/`*_TYPES`/filenames are parallel structures that can drift

**File:** `src/fleet_analytics/ingest.py:66-68`; `src/fleet_analytics/config.py:35-62`
**Issue:** `ingest_bronze` lists the three `_create_bronze` calls literally, while `EXPECTED_ROWS` keys (`bronze_availability`/...), the `*_TYPES` maps, and the `*_CSV` filenames are maintained as separate structures. The table-name string `"bronze_availability"` is repeated as a literal in ingest.py, profile.py, the tests, and as an `EXPECTED_ROWS` key. A rename in one place silently de-syncs the others (the row-count loop would simply not cover an untracked table).
**Fix:** Consider a single source-of-truth table definition (name → filename → types → expected_rows) iterated by `ingest_bronze` and the row-count loop, so the three concerns cannot drift apart.

### IN-05: `availability_max == 1.0` / `availability_min == 0.0` rely on exact float equality

**File:** `tests/test_profile.py:30-31`
**Issue:** Asserting `facts["availability_max"] == 1.0` and `== 0.0` is exact float equality. It is correct on this data (literal `1` and `0` values exist, and DuckDB returns them as exact `1.0`/`0.0`), so this is not currently a defect. Noted because exact float equality on aggregates is fragile if the column ever holds computed (non-literal) extremes.
**Fix:** No action required for the current source. If extremes ever become derived values, switch to `pytest.approx`.

---

_Reviewed: 2026-06-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
