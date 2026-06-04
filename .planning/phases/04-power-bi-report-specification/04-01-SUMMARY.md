---
phase: 04-power-bi-report-specification
plan: 01
subsystem: data-engineering / power-bi-handoff
tags: [reference-dimension, dim_class_target, audit-targets, unit_type-bridge, duckdb-copy, pytest-guard]
requires:
  - "src/fleet_analytics/config.py (ASSET_CLASS_TARGETS, UNIT_TYPE_TO_CLASS, GOLD_DIR)"
  - "src/fleet_analytics/kpis.py (_class_targets_relation VALUES idiom)"
  - "src/fleet_analytics/export.py (COPY-to-Parquet+CSV idiom)"
provides:
  - "data/gold/dim_class_target.parquet (+ .csv) — committed reference dimension"
  - "src/fleet_analytics/class_target.py (build_class_target / write_class_target)"
  - "dim_class_target[unit_type] -> fact_vehicle[UNIT_TYPE] relationship (for Plans 02/03)"
affects:
  - "tests/conftest.py (gold fixture now builds dim_class_target)"
tech-stack:
  added: []
  patterns:
    - "config dict -> ?-bound VALUES relation (reused from kpis._class_targets_relation)"
    - "DuckDB COPY type-fidelity export (Parquet primary, CSV secondary)"
    - "second :memory: connection parquet roundtrip guard in try/finally"
key-files:
  created:
    - "src/fleet_analytics/class_target.py"
    - "data/gold/dim_class_target.parquet"
    - "data/gold/dim_class_target.csv"
    - "tests/test_class_target.py"
  modified:
    - "tests/conftest.py"
decisions:
  - "dim_class_target keyed on UNIT_TYPE (5-row bridge), NOT CATEGORY_CLASS — matches validated Phase-3 KPI join"
  - "5-row grain (one per audit class), not 10 — config.UNIT_TYPE_TO_CLASS maps 5 unit types 1:1 to 5 classes"
  - "Kept OFF config.GOLD_TABLES so the existing 5-table export contract and GOLD_EXPECTED_ROWS stay green"
metrics:
  duration: ~12 min
  completed: 2026-06-04
  tasks: 2
  files: 5
---

# Phase 4 Plan 01: dim_class_target Reference Dimension Summary

Built the committed `dim_class_target` reference dimension — a config-sourced, type-preserving (Parquet + CSV) audit-target table keyed on `UNIT_TYPE` — and locked the 5 audit targets (Light 95 / Medium 92 / Heavy 85 / Off-Road 88 / Other 90) with a parametrized pytest guard plus a Parquet roundtrip, resolving the 04-PATTERNS.md `UNIT_TYPE`-vs-`CATEGORY_CLASS` join-key discrepancy in code.

## What Was Built

- **`src/fleet_analytics/class_target.py`** — `build_class_target(con)` materializes a `dim_class_target` DuckDB table from a `?`-bound `(VALUES (?, ?, ?), ...) AS ct(unit_type, class_label, target)` relation (the exact `kpis._class_targets_relation()` shape), sourced solely from `config.UNIT_TYPE_TO_CLASS` + `config.ASSET_CLASS_TARGETS`. `write_class_target(con)` mirrors `export.py`'s two-statement COPY idiom (Parquet primary, CSV readable secondary). No target value is ever inlined into the SQL string.
- **`data/gold/dim_class_target.{parquet,csv}`** — the committed reference dimension (columns: `unit_type`, `class_label`, `target`), 5 rows, one per audit class.
- **`tests/test_class_target.py`** — `test_class_target_rows` (5 rows, 5 distinct labels), a 5-case `@pytest.mark.parametrize` over the exact `(class_label, target)` audit pairs, and `test_class_target_parquet_roundtrip` (re-reads the committed Parquet via a second `:memory:` connection in `try/finally`, asserts Heavy → 85).
- **`tests/conftest.py`** — one added line wires `class_target.build_class_target(con)` into the session-scoped `gold` fixture after `kpis.build_all(con)`.

## Grain / Key Decision (resolves D-03/D-04)

The committed table is a **bridge keyed on `unit_type`**, relating
`dim_class_target[unit_type] -> fact_vehicle[UNIT_TYPE]`. This matches the validated
Phase-3 KPI layer exactly (`kpis.py` joins targets on `fv.UNIT_TYPE = ct.unit_type`).

**Why `CATEGORY_CLASS` was rejected:** `fact_vehicle.CATEGORY_CLASS` holds 19 granular
codes (CLASS1-8, APPARATUS, ATTACHMENT, BOAT, CONSTRUCT, FACILITY, GROUND, LIFTING,
ROADMAIN, TRAILER, TRAM, WINTERMAIN) — not the 5 audit labels. A
`dim_class_target[category_class] -> fact_vehicle[CATEGORY_CLASS]` relationship would be
a 19-vs-5 cardinality mismatch and would NOT reproduce the validated by-class
availability targets. The 5 audit labels live one level up via `UNIT_TYPE`.

**Exported file paths (for Plans 02/03 to reference):**
- `data/gold/dim_class_target.parquet`
- `data/gold/dim_class_target.csv`
- Power BI relationship: `dim_class_target[unit_type]` → `fact_vehicle[UNIT_TYPE]` (one-to-many; the target line in the availability-by-class visual joins through this).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan asserted 10 rows; correct grain is 5 rows**
- **Found during:** Task 1 (running the plan's verify command, which asserted `(10, 5, 5)`).
- **Issue:** The plan's `<behavior>` and verify command expected `dim_class_target` to have exactly 10 rows ("one per UNIT_TYPE in config.UNIT_TYPE_TO_CLASS"). But `config.UNIT_TYPE_TO_CLASS` contains exactly **5** entries (LIGHT DUTY, MEDIUM DUTY, HEAVY DUTY, OFF-ROAD, OTHER), each mapping 1:1 to one of the 5 audit classes. Iterating that dict yields 5 rows, not 10 — the builder produced `(5, 5, 5)`, and the assertion `==(10,5,5)` was unachievable from the real config. 04-PATTERNS.md option (a) loosely described a "10/19 → 5 mapping," but the actual config maps only the 5 audit-relevant unit types, so the bridge is a clean 5→5.
- **Fix:** Aligned the verify expectation and the `test_class_target_rows` row-count assertion to `(5, 5)` — the correct, defensible grain. The 5-row table still fully satisfies every must-have (5 distinct class labels, 5 distinct audit targets, keyed on `UNIT_TYPE`, reproduces the validated Phase-3 KPI join which uses the identical 5-row `_class_targets_relation()`). No change to the builder implementation was required — the builder was correct; only the plan's assertion target was wrong.
- **Files modified:** none beyond the planned `class_target.py` / `test_class_target.py` (the fix was in the expected value, not the code).
- **Commits:** 7f61069 (Task 1), 3e541bb (Task 2).

### Out-of-scope observation (not fixed)

- Running the existing test suite (`test_export.py::test_ten_files_written` and the parquet/csv type tests call `export.write_gold`) rewrites the 5 pre-existing Gold CSVs with CRLF line endings on Windows, producing whitespace-only `git diff` noise (`--ignore-all-space` shows zero content change). This is pre-existing test behavior unrelated to this plan; those files were restored (`git checkout --`) and left untouched. Not a regression in this plan's scope.

## Verification

- `uv run pytest tests/test_class_target.py tests/test_export.py tests/test_dimensions.py -q` → 13 passed.
- `uv run pytest -q` (full suite) → **76 passed** (existing 5-table export contract unbroken; `dim_class_target` NOT added to `GOLD_TABLES`).
- `data/gold/dim_class_target.{parquet,csv}` exist and re-read clean (roundtrip test: Heavy → 85).
- `class_target.py` module docstring documents the `UNIT_TYPE` (not `CATEGORY_CLASS`) key decision and audit-cited provenance.

## Threat Model Compliance

- **T-04-01 (Tampering, target values):** mitigated — values `?`-bound from `config.ASSET_CLASS_TARGETS` (no literal 95/92/85/88/90 in any SQL string); `test_class_target_value` parametrized guard asserts all 5 exact values so any drift fails CI.
- **T-04-02 (Info Disclosure, COPY path interpolation):** accepted as planned — only `config.GOLD_DIR`-derived internal paths and the literal table name are interpolated; no external/user value reaches the SQL string (same guarantee as `export.py`).
- **T-04-SC (uv/PyPI installs):** no new dependencies introduced; reused already-pinned duckdb/pytest.

## Known Stubs

None. The table is fully data-backed from audit-cited config constants.

## TDD Gate Compliance

Both tasks carried `tdd="true"`. Task 1's verification is a standalone runtime assertion (per the plan's `<verify><automated>`), satisfied green after the Rule-1 row-count correction. Task 2 added the falsifiable pytest guard (RED→GREEN: the test file + fixture wiring were authored to assert the audit values, and the full suite passed on first run since the builder from Task 1 already produced the correct table). The `test(04-01): ...` commit (3e541bb) records the guard.

## Self-Check: PASSED

- FOUND: src/fleet_analytics/class_target.py
- FOUND: data/gold/dim_class_target.parquet
- FOUND: data/gold/dim_class_target.csv
- FOUND: tests/test_class_target.py
- FOUND commit: 7f61069 (Task 1 — feat)
- FOUND commit: 3e541bb (Task 2 — test)
