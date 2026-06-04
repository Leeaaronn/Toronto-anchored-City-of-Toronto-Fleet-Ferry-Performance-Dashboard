---
phase: 04-power-bi-report-specification
reviewed: 2026-06-04T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/fleet_analytics/class_target.py
  - tests/test_class_target.py
  - tests/conftest.py
  - deliverables/report_spec.md
findings:
  critical: 2
  warning: 3
  info: 1
  total: 6
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-06-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the `dim_class_target` builder, its pytest guard, the `conftest.py` fixture
extension, and the `report_spec.md` Power BI build contract.

The builder logic and export idiom are correct. The most serious defects are a stale
"10-row" grain claim in two docstring locations (contradicted by the actual 5-row config
and every test/summary artifact) and a semantically broken `Gap to Target` DAX measure in
the report spec that silently returns the raw availability rate instead of the signed gap
whenever more than one class is in the filter context.

Two warnings concern test-isolation hygiene (the roundtrip test mutates the committed
Parquet artifact from the shared session fixture) and a slicer field choice that labels
19-code `CATEGORY_CLASS` as "Asset Class" while the rest of the spec routes audit-class
analysis through `UNIT_TYPE`.

---

## Critical Issues

### CR-01: Module and function docstrings claim "10-row bridge" — actual grain is 5 rows

**File:** `src/fleet_analytics/class_target.py:10-11` and `:45`

**Issue:** The module docstring states `dim_class_target is a **10-row bridge keyed on
unit_type**`. The function docstring at line 45 repeats `(10-row UNIT_TYPE bridge)`.
`config.UNIT_TYPE_TO_CLASS` contains exactly 5 entries; the builder iterates that dict
and produces 5 rows; `test_class_target_rows` asserts `total == 5`; the 04-01-SUMMARY.md
explicitly documents that the plan's 10-row assertion was a bug corrected to 5. The
documented grain (5 rows, one per audit class) and the shipped grain (5 rows) are correct
— the docstrings are stale artefacts from before the Rule-1 correction and were never
updated.

A reader of the module docstring and function signature in isolation will believe the
table has 10 rows when it has 5. Any downstream doc or schema assertion seeded from these
docstrings will embed an incorrect row count.

**Fix:** Update both locations to "5-row bridge":

```python
# module docstring line 10-11 — replace:
``dim_class_target`` is a **10-row bridge keyed on ``unit_type``**, NOT a 5-row

# with:
``dim_class_target`` is a **5-row bridge keyed on ``unit_type``**

# function docstring line 45 — replace:
"""Register ``dim_class_target`` on ``con`` from config (10-row UNIT_TYPE bridge).

# with:
"""Register ``dim_class_target`` on ``con`` from config (5-row UNIT_TYPE bridge).
```

---

### CR-02: `Gap to Target` DAX in A2 (report_spec.md) silently returns the wrong value when multiple classes are in scope

**File:** `deliverables/report_spec.md:127`

**Issue:** The specified measure is:

```DAX
Gap to Target = [Availability Rate by Class] - DIVIDE ( [Class Target], 100 )
```

where:

```DAX
Class Target = SELECTEDVALUE ( dim_class_target[target] )
```

`SELECTEDVALUE` returns BLANK when more than one value is present in the filter context
(e.g. the Page 3 Summary tile showing all classes, or a matrix cell spanning multiple
classes, or a card visual before any slicer selection). In those cases `DIVIDE(BLANK(),
100)` evaluates to 0, and `Gap to Target` silently returns `[Availability Rate by Class]`
unmodified — a positive fraction around 0.89 — instead of the signed gap. No error is
raised; the value is simply wrong.

The `Availability Rate by Class` measure has the same problem in a non-class-filtered
context: it computes the pooled rate over all unfiltered rows, identical to A1, which is
explicitly warned against in the A1 footnote ("mean-of-class-means 0.8786 is the WRONG
total"). The slicer plan (Slicer Plan, line 111) and the A2 visual description assume a
class axis/slicer provides the necessary filter context, but the Page 3 reuse of A2
measures (Page 3, row 1 — `[Gap to Target]` reused) and any standalone card use will
produce incorrect output silently.

The correct Power BI pattern for "gap to the per-row related target" is to drive the
computation through the relationship with `RELATED` inside a `SUMX`/`AVERAGEX` iteration
rather than relying on `SELECTEDVALUE`:

**Fix:** Revise the A2 DAX block to a formulation that is safe in all filter contexts:

```DAX
-- Replace the SELECTEDVALUE-based measures with:

Class Target (Row) =
    RELATED ( dim_class_target[target] )
    -- use only in row-context (matrix cell / SUMX); not a standalone measure

Avg Class Target =
    AVERAGEX (
        VALUES ( fact_vehicle[UNIT_TYPE] ),
        RELATED ( dim_class_target[target] )
    )

Gap to Target =
    [Availability Rate by Class]
        - DIVIDE (
            AVERAGEX (
                VALUES ( fact_vehicle[UNIT_TYPE] ),
                RELATED ( dim_class_target[target] )
            ),
            100
        )
```

For the bullet/bar-with-target-line visual specifically (one class per axis category),
`SELECTEDVALUE` is fine on the target line because each bar row has exactly one class in
context. Add an explicit `SELECTEDVALUE(..., BLANK())` fallback note and document that
the measure is axis-context-dependent and must not be placed on a card without a class
slicer.

---

## Warnings

### WR-01: `test_class_target_parquet_roundtrip` mutates the committed Gold artifact from the shared session fixture

**File:** `tests/test_class_target.py:52`

**Issue:** The test calls `class_target.write_class_target(gold)`, which executes two
`COPY` statements that overwrite `data/gold/dim_class_target.parquet` and
`data/gold/dim_class_target.csv` on disk. The `gold` fixture is session-scoped and shared
across the entire test suite. Overwriting the committed reference files from within a test
has two problems:

1. It pollutes the working tree during every test run (even `pytest -q`), making the
   repository appear dirty. The 04-01-SUMMARY.md already documents that the analogous
   `test_export.py` side effect causes CRLF `git diff` noise that required a manual
   `git checkout --` restore.
2. If the test run is interrupted after `write_class_target` but before the session ends,
   the committed files may be left in a modified state.

The roundtrip guard's actual intent is to verify that the committed Parquet reads back
correctly — it does not need to regenerate the file from the shared fixture connection.
The regeneration path belongs in a dedicated writer test that builds its own `:memory:`
connection, writes to a temp path, and reads back.

**Fix:** Use a `tmp_path`-scoped connection for the write, not the shared `gold` fixture:

```python
def test_class_target_parquet_roundtrip(tmp_path: pathlib.Path) -> None:
    """The Parquet roundtrip is correct: write to tmp, read back Heavy -> 85."""
    con = duckdb.connect(":memory:")
    try:
        class_target.build_class_target(con)
        # Write to a temp location, not the committed Gold directory.
        p = (tmp_path / "dim_class_target").as_posix()
        con.execute(f"COPY (SELECT * FROM dim_class_target) TO '{p}.parquet' (FORMAT PARQUET)")
        rd = duckdb.connect(":memory:")
        try:
            heavy_target = rd.execute(
                "SELECT target FROM read_parquet(?) WHERE class_label = 'Heavy'",
                [f"{p}.parquet"],
            ).fetchone()[0]
        finally:
            rd.close()
    finally:
        con.close()
    assert heavy_target == 85
```

---

### WR-02: Slicer Plan uses `CATEGORY_CLASS` labeled as "Asset Class" — inconsistent with the UNIT_TYPE axis used throughout the Fleet Maintenance page

**File:** `deliverables/report_spec.md:111`

**Issue:** The Slicer Plan specifies:

```
fact_vehicle[CATEGORY_CLASS]  (Asset Class)  Dropdown (multi-select)  Synced across all pages
```

The same document, in the Column Reference Reconciliation table (line 22), explicitly
documents that `CATEGORY_CLASS` holds **19 granular codes** (CLASS1-8, APPARATUS,
ATTACHMENT, BOAT, CONSTRUCT, FACILITY, GROUND, LIFTING, ROADMAIN, TRAILER, TRAM,
WINTERMAIN) and **not** the 5 audit labels. The audit-class analysis throughout Pages 1-3
uses `fact_vehicle[UNIT_TYPE]` as the axis and relationship key.

The effect of this inconsistency is that the "Asset Class" slicer exposes 19 granular
codes to the user (e.g. "CLASS1", "CLASS2", "APPARATUS") rather than the 5 readable
audit labels (Light, Medium, Heavy, Off-Road, Other). Selecting "CLASS1" from the slicer
does NOT correspond to the "Light" class bar in A2, because A2 uses `UNIT_TYPE` on its
axis. The slicer and the chart axis operate on different columns; the slicer will appear
to have no cross-filter effect on the class chart.

**Fix:** Align the slicer to the same dimension used for class analysis:

```
| All 3 pages | fact_vehicle[UNIT_TYPE]  (Asset Class — 5 audit labels)
              | Dropdown (multi-select) | Synced across all pages |
```

If exposure of granular sub-class codes is genuinely desired, add a separate secondary
slicer labeled "Category Class (granular)" and document that it is a drill-through filter,
not the primary audit-class filter. Do not label CATEGORY_CLASS as "Asset Class" when
the audit-class labels live on UNIT_TYPE.

---

### WR-03: `conftest.py` `gold` fixture returns `con` without yielding — teardown never runs for `gold`

**File:** `tests/conftest.py:23-44`

**Issue:** The `gold` fixture uses `return con` (line 44) rather than `yield con`. Because
there is no yield, pytest has no opportunity to run any teardown code for the `gold`
fixture scope. Currently `gold` has no teardown of its own, so this causes no immediate
failure, but it breaks the pytest fixture contract: if any future maintainer adds cleanup
(e.g. `DROP TABLE dim_class_target`) after the yield, `return` will silently skip it.
The parent `con` fixture correctly uses `yield` + `connection.close()` (lines 16-19).
The inconsistency also means static analysis tools and pytest plugins that inspect fixture
teardown will mis-report this fixture.

**Fix:**

```python
@pytest.fixture(scope="session")
def gold(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    from fleet_analytics import class_target, kpis, model, transform

    transform.build_all(con)
    model.build_all(con)
    kpis.build_all(con)
    class_target.build_class_target(con)
    yield con   # <-- yield, not return; keeps teardown path open
```

---

## Info

### IN-01: `write_class_target` interpolates path string into SQL — inconsistent with the `?`-bound value idiom, though within the documented security boundary

**File:** `src/fleet_analytics/class_target.py:83-86`

**Issue:** `write_class_target` builds the COPY path via f-string interpolation:

```python
p = (config.GOLD_DIR / "dim_class_target").as_posix()
con.execute(f"COPY (SELECT * FROM dim_class_target) TO '{p}.parquet' (FORMAT PARQUET)")
```

The module docstring and the security note correctly document that only internal
`config.GOLD_DIR`-derived paths are interpolated — no external/user value reaches the SQL
string. This matches the `export.py` idiom. However, `build_class_target` uses `?`-bound
params for all data values, so a reader comparing the two functions sees inconsistent
treatment: values are bound, paths are interpolated. The inconsistency is not a security
defect (path is from config only) but could mislead a maintainer who adds a user-supplied
path into the same pattern.

`export.py` uses the same interpolation pattern and is tested; flagging for awareness
only.

**Fix (optional):** Add a brief inline comment at the interpolation site referencing the
security note, the same way `export.py` lines 18-21 document the guarantee:

```python
# Only config.GOLD_DIR-derived internal path is interpolated (no external value).
p = (config.GOLD_DIR / "dim_class_target").as_posix()
```

---

_Reviewed: 2026-06-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
