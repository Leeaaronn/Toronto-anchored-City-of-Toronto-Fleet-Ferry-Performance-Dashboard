---
phase: 02-transform-model-join-integrity
reviewed: 2026-06-02T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - src/fleet_analytics/config.py
  - src/fleet_analytics/transform.py
  - src/fleet_analytics/model.py
  - src/fleet_analytics/export.py
  - tests/conftest.py
  - tests/test_derived_fields.py
  - tests/test_join_integrity.py
  - tests/test_dimensions.py
  - tests/test_export.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-02
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The Phase-2 production code (`config.py`, `transform.py`, `model.py`, `export.py`) is
clean and correct. All locked correctness invariants from the domain context are
respected: `TRY_CAST` (not `CAST`) preserves the 44 alphanumeric units with NULL keys;
`AVAILABILITY_YTD`'s 209 NULLs flow through staging → join → export with no
`COALESCE`/`fillna`; the availability-anchored `LEFT JOIN` cannot fan out (and is
double-guarded by the row-count assertion loop in `model.build_all`); `dim_date`
(4,383) and `dim_time` (96) generate-series spines are arithmetically correct
(verified inclusive day count == 4,383); and SQL interpolation in `export.py`/`model.py`
draws only from internal `config` constants, so there is no injection surface from
external values. No BLOCKER-tier defects were found.

The substantive findings are in the **test layer**, not the pipeline. Two issues are
material:

1. The derived-field tests (`test_fleet_age`, `test_season`, `test_season_daypart`)
   re-execute the transform's SQL expressions against synthetic literals instead of
   asserting against the columns `transform.py` actually produced. They would stay
   green even if the real `fleet_age` / `season` / `daypart` column expressions were
   broken — so they do not guard the implementation they claim to gate.
2. `test_export.py` writes the 10 Gold files directly into `data/gold/`, which is a
   **git-tracked deliverable directory**. Running the suite mutates committed output
   files in place, with no temp dir and no cleanup.

## Warnings

### WR-01: Derived-field tests validate synthetic SQL, not the produced columns

**File:** `tests/test_derived_fields.py:80-110`
**Issue:** `test_fleet_age` asserts on `gold.execute("SELECT ? - ?", [REFERENCE_YEAR, year])`
— it computes the expected arithmetic in isolation and never reads
`stg_availability.fleet_age`. Likewise `test_season` (line 94-97) and
`test_season_daypart` (line 107-110) re-run copies of the `CASE` expressions against
synthetic literal timestamps via `_SEASON_SQL` / `_DAYPART_SQL`, never querying the
`season` / `daypart` columns on `stg_ferry`. If the real expression in `transform.py`
were changed to, say, `YEAR - REFERENCE_YEAR` or a shifted month boundary, every one of
these tests would still pass. They are tautologies over duplicated logic, not
regression guards on the built tables. (`test_gap_signed` at line 113-123 is the
correct pattern — it asserts against the actual `stg_ferry.sales_redemption_gap`
column; the others should follow it.)
**Fix:** Assert against the produced columns. For example:
```python
def test_fleet_age_against_column(gold):
    # No fleet_age row may disagree with REFERENCE_YEAR - YEAR.
    mismatched = gold.execute(
        "SELECT COUNT(*) FROM stg_availability "
        "WHERE fleet_age <> ? - YEAR",
        [config.REFERENCE_YEAR],
    ).fetchone()[0]
    assert mismatched == 0
```
Apply the same "compare the real column to an independent recomputation" shape to
`season` and `daypart` (e.g. `WHERE season <> CASE ... END`), so a change to the
embedded SQL in `transform.py` actually fails a test.

### WR-02: Export tests write into the git-tracked `data/gold/` deliverable directory

**File:** `tests/test_export.py:40-46, 55, 88` (and `export.write_gold` → `config.GOLD_DIR`)
**Issue:** `export.write_gold(gold)` writes to `config.GOLD_DIR` = `PROJECT_ROOT/data/gold`,
which is checked into git (all 10 `*.parquet` / `*.csv` files are tracked). Each of the
three export tests calls `write_gold` against that real path with no `tmp_path` redirect
and no cleanup, so simply running `pytest` overwrites committed deliverable files in the
working tree. This couples test execution to repo state, can produce spurious `git diff`
noise on the deliverable, and risks a developer committing test-run output. Test side
effects must not touch tracked artifacts.
**Fix:** Redirect `config.GOLD_DIR` to a temp directory for the duration of the test,
e.g. with a fixture:
```python
@pytest.fixture()
def gold_dir(tmp_path, monkeypatch):
    d = tmp_path / "gold"
    monkeypatch.setattr(config, "GOLD_DIR", d)
    return d
```
and have the export tests depend on it so writes land under `tmp_path` and are discarded
after the run.

### WR-03: `write_gold` interpolates `GOLD_DIR` path into single-quoted SQL without escaping

**File:** `src/fleet_analytics/export.py:44-46`
**Issue:** The output path is interpolated into the COPY statement as
`TO '{p}.parquet'`. `p` derives from `config.GOLD_DIR` (internal, not external input),
so this is not a user-driven injection vector today — but a single quote, backslash, or
other special character anywhere in the resolved absolute path (e.g. a checkout under a
directory containing `'`) would break the SQL string or change its meaning. The COPY
target should not be string-built. (The table name in `SELECT * FROM {t}` is lower-risk
since it comes from the fixed `GOLD_TABLES` list, but the path is the weak spot.)
**Fix:** Pass the path as a bound parameter / use DuckDB's parameterized COPY, or at
minimum escape embedded quotes:
```python
con.execute(
    "COPY (SELECT * FROM " + t + ") TO ? (FORMAT PARQUET)",
    [f"{p}.parquet"],
)
```
(Confirm the installed DuckDB version accepts a bound parameter for the COPY target; if
not, escape the path with `p.replace("'", "''")` before interpolation.)

### WR-04: `test_fact_unique_key` assumes availability `UNIT_NO` is unique but never asserts it on the source

**File:** `tests/test_join_integrity.py:49-54`
**Issue:** The test asserts `COUNT(*) == COUNT(DISTINCT UNIT_NO) == 4614` on
`fact_vehicle`. This is meant to prove "no fan-out," but it conflates two facts: that the
join did not duplicate rows, AND that `UNIT_NO` was already unique in
`bronze_availability`. If a future CSV re-supply introduced a duplicate availability
`UNIT_NO`, this test would fail and be misread as a join fan-out regression, while a real
join fan-out via a duplicated *utilization* `unit_key_int` would not be isolated here.
The actual fan-out guard is the `COUNT(*) == 4614` row-count check (line 39-46 and the
`model.build_all` assertion loop), which is sound.
**Fix:** Make the intent explicit by adding a direct source-uniqueness assertion and a
fan-out assertion that targets the join key rather than `UNIT_NO`:
```python
def test_util_key_unique_no_fanout(gold):
    dup_keys = gold.execute(
        "SELECT COUNT(*) FROM ("
        " SELECT unit_key_int FROM stg_utilization "
        " WHERE unit_key_int IS NOT NULL "
        " GROUP BY unit_key_int HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    assert dup_keys == 0
```

## Info

### IN-01: Mid-module `import pytest` with manual `# noqa: E402`

**File:** `tests/test_derived_fields.py:72`
**Issue:** `import pytest` is placed in the middle of the module (after function
definitions) and suppressed with `# noqa: E402`. The module already imports at the top;
this second import only exists to sit near the parametrized tests. It is dead-weight that
requires a lint suppression.
**Fix:** Move `import pytest` to the top import block with `from fleet_analytics import config`
and delete the `# noqa: E402`.

### IN-02: `con` / `gold` fixtures are typed as `DuckDBPyConnection` but are generators

**File:** `tests/conftest.py:15, 23`
**Issue:** `def con(...) -> duckdb.DuckDBPyConnection` uses `yield`, so the declared return
type does not match the actual generator. Harmless at runtime (pytest handles it), but a
type checker will flag the annotation as incorrect.
**Fix:** Annotate as `Iterator[duckdb.DuckDBPyConnection]` (from `collections.abc`) for the
`yield`-based fixture, or drop the return annotation.

### IN-03: `_scalar` helper duplicated across test modules

**File:** `tests/test_join_integrity.py:17-19` (and the `gold.execute(...).fetchone()[0]`
idiom repeated in `test_dimensions.py`, `test_derived_fields.py`, `test_export.py`)
**Issue:** The `con.execute(sql).fetchone()[0]` scalar-fetch pattern is re-implemented or
inlined in every test file. Minor duplication.
**Fix:** Promote a single `scalar(con, sql, params=None)` helper into `conftest.py` (or a
small `tests/_util.py`) and import it where needed.

---

_Reviewed: 2026-06-02_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
