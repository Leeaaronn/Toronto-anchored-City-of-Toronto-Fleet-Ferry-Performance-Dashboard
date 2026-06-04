---
phase: 04-power-bi-report-specification
fixed_at: 2026-06-04T20:34:08Z
review_path: .planning/phases/04-power-bi-report-specification/04-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-06-04T20:34:08Z
**Source review:** .planning/phases/04-power-bi-report-specification/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (CR-01, CR-02, WR-01, WR-02, WR-03; IN-01 excluded per scope)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: Module and function docstrings claim "10-row bridge" — actual grain is 5 rows

**Files modified:** `src/fleet_analytics/class_target.py`
**Commit:** 4959fb5
**Applied fix:** Replaced "10-row bridge" with "5-row bridge" in two locations: (1) module docstring line 10 — `dim_class_target is a **5-row bridge keyed on unit_type**, NOT a category_class dim.`; (2) `build_class_target` function docstring — `Register dim_class_target on con from config (5-row UNIT_TYPE bridge).`. The "NOT a 5-row category_class dim" phrasing was adjusted to "NOT a category_class dim" to avoid the now-redundant "5-row vs 5-row" comparison while preserving the intent.

---

### CR-02: `Gap to Target` DAX silently returns wrong value when multiple classes are in scope

**Files modified:** `deliverables/report_spec.md`
**Commit:** 1aa06c9
**Applied fix:** In the A2 visual row of Page 1, replaced `Class Target = SELECTEDVALUE ( dim_class_target[target] )` with `Class Target = AVERAGEX ( VALUES ( fact_vehicle[UNIT_TYPE] ), RELATED ( dim_class_target[target] ) )`. Updated `Gap to Target` to inline the `AVERAGEX` expression directly: `Gap to Target = [Availability Rate by Class] - DIVIDE ( AVERAGEX ( VALUES ( fact_vehicle[UNIT_TYPE] ), RELATED ( dim_class_target[target] ) ), 100 )`. The SQL validation values (signed gaps Light -0.0351 / Medium -0.0588 / Heavy -0.0552 / Off-Road +0.0082 / Other +0.0337) remain correct since the AVERAGEX form produces identical values per-class. The D-04 reconciliation table reference to SELECTEDVALUE on line 21 was left intact — it is a documentation row explaining the placeholder correction, not a live measure spec. Status: requires human verification (logic change to DAX; values are mathematically equivalent per-class but the filter-context safety semantics are the point of the fix).

---

### WR-01: `test_class_target_parquet_roundtrip` mutates the committed Gold artifact

**Files modified:** `tests/test_class_target.py`
**Commit:** cbfa411
**Applied fix:** Rewrote `test_class_target_parquet_roundtrip` to accept `tmp_path: pathlib.Path` as its only argument (no `gold` fixture dependency). The test creates its own `:memory:` DuckDB connection, calls `build_class_target(con)` to populate `dim_class_target`, writes to `(tmp_path / "dim_class_target").as_posix() + ".parquet"` via a direct COPY statement, then reads back via a second `:memory:` connection. Added `import pathlib` to the file's imports. After the fix, `data/gold/dim_class_target.{parquet,csv}` are no longer touched during `pytest` runs. Confirmed by `git status` — those files show no working-tree churn post-test.

---

### WR-02: Slicer Plan uses `CATEGORY_CLASS` labeled as "Asset Class"

**Files modified:** `deliverables/report_spec.md`
**Commit:** 8d93edb
**Applied fix:** In the Slicer Plan table, replaced the "Asset Class" slicer row from `` `fact_vehicle[CATEGORY_CLASS]` (Asset Class) `` to `` `fact_vehicle[UNIT_TYPE]` (Asset Class — 5 audit labels) ``. The D-04 Column Reference Reconciliation documentation rows (which explain that CATEGORY_CLASS holds 19 granular codes and that the audit-class labels live on UNIT_TYPE) were left intact — those are informational documentation rows, not live slicer specifications.

---

### WR-03: `gold` fixture uses `return con` instead of `yield con`

**Files modified:** `tests/conftest.py`
**Commit:** 20c581b
**Applied fix:** Changed the final line of the `gold` fixture from `return con` to `yield con`, matching the parent `con` fixture's generator pattern. No teardown code follows the yield so there is no behavioral change — the fix opens the teardown path for future maintainers and makes static analysis tools report the fixture correctly.

---

## Verification

**Test suite result:** 76 passed in 7.29s (no regressions).
**Working tree after tests:** `data/gold/dim_class_target.{parquet,csv}` — no churn (WR-01 fix confirmed effective). Other `data/gold/*.csv` files show CRLF line-ending warnings only (pre-existing condition from the test_export.py side-effect documented in 04-01-SUMMARY.md; not introduced by these fixes).

---

_Fixed: 2026-06-04T20:34:08Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
