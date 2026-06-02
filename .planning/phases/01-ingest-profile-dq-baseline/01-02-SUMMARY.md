---
phase: 01-ingest-profile-dq-baseline
plan: 02
subsystem: data-quality
tags: [pandera, duckdb, pytest, data-quality, dq-contract, validation, regression-guard]

# Dependency graph
requires:
  - "01-01 (Bronze ingest, config.py value sets, conftest `con` fixture)"
provides:
  - "src/fleet_analytics/schemas.py — Pandera DataFrameSchemas (availability/utilization/ferry DQ contracts)"
  - "tests/test_schemas.py — DATA-04 regression guards (0–1 bounds, value sets, dtypes)"
  - "Executable enforcement of: AVAILABILITY_YTD ∈ [0,1] nullable; Utilization/Specialized value sets; UNIT_NO str + AVAILABILITY_YTD float dtypes"
affects:
  - "01-03 (DQ report — documents the same facts these schemas enforce)"
  - "Phase 2 (schemas reusable as the in-test contract for transformed/joined tables)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pandera DataFrameSchema as the single declarative DQ contract (no hand-rolled assert ladders)"
    - "strict=False schemas validate only load-bearing columns; Bronze extras pass through"
    - "Check.in_range(0.0,1.0) + nullable=True encodes 'the 209 nulls are legal' as a contract"
    - "Check.isin value-set guards on pre-applied categoricals (Utilization, Specialized units)"
    - "pandas 3.0 StringDtype-aware dtype assertion via pd.api.types.is_string_dtype"

key-files:
  created:
    - "src/fleet_analytics/schemas.py"
    - "tests/test_schemas.py"
  modified: []

key-decisions:
  - "Imported `import pandera.pandas as pa` + Column/Check/DataFrameSchema from pandera.pandas (Pandera 0.31.1 namespaced API)"
  - "AVAILABILITY_YTD: Check.in_range(0.0,1.0) with nullable=True — assert the bound, never clamp; nulls stay legal (DATA-03)"
  - "strict=False on all three schemas so Bronze's extra columns are tolerated (only contracted columns validated)"
  - "dtype guard uses pd.api.types.is_string_dtype (not == object) — pandas 3.0 + DuckDB surfaces VARCHAR as StringDtype"

patterns-established:
  - "Pattern: one Pandera schema per Bronze table = the documented-AND-enforced DQ contract"
  - "Pattern: schema.validate(frame) inside pytest — passing validate is the green signal, SchemaError fails the test"

requirements-completed: [DATA-04, DATA-01]

# Metrics
duration: 2min
completed: 2026-06-02
---

# Phase 01 Plan 02: Pandera DQ Contracts Summary

**Froze the DATA-04 data-quality contracts as declarative Pandera schemas (availability 0–1 bounds with legal nulls, utilization value sets, explicit dtypes) and locked them with 4 green pytest regression guards — full suite now 15 passing.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-02T19:11:36Z
- **Completed:** 2026-06-02T19:13:09Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments

- Authored `src/fleet_analytics/schemas.py` with three Pandera `DataFrameSchema`s — the single declarative source of the Bronze DQ contracts (no hand-rolled assert ladders, per RESEARCH "Don't Hand-Roll").
  - `availability_schema`: `AVAILABILITY_YTD` float `Check.in_range(0.0, 1.0)` `nullable=True` (the 209 blanks are legal — DATA-03), `UNIT_NO` str non-null, `CATEGORY_CLASS` str non-null.
  - `utilization_schema`: `Utilization` `Check.isin({Underutilized, Not Underutilized})`, `Specialized units` `Check.isin({Yes, No})`, `UNIT_NO` str non-null.
  - `ferry_schema`: `Timestamp` datetime, `Sales Count` / `Redemption Count` integer, all non-null.
- Wrote `tests/test_schemas.py` (4 guards) validating each Bronze frame through its schema via the session `con` fixture: `test_availability_bounds`, `test_value_sets`, `test_dtypes`, `test_ferry_schema` — names aligned to the 01-VALIDATION Per-Task Verification Map.
- Confirmed the explicit-type ingest held: `UNIT_NO` is a string dtype (zero-padding preserved) and `AVAILABILITY_YTD` is float.
- Full suite green: `uv run pytest -q` → 15 passed (11 from 01-01 + 4 new).

## Task Commits

Each task was committed atomically:

1. **Task 1: Pandera schemas for the three Bronze tables (DATA-04 contracts)** — `ed78817` (feat)
2. **Task 2: Pandera validation tests — bounds, value sets, dtypes (DATA-04)** — `f1f3dd5` (test)

_Both are tdd tasks. Task 1 RED was structural (module absent) → GREEN on import. Task 2 produced a genuine RED on the dtype assertion (see Deviations) before going green._

## Files Created/Modified

- `src/fleet_analytics/schemas.py` — three Pandera `DataFrameSchema`s; `import pandera.pandas as pa`; `AVAILABILITY_YTD` `Check.in_range(0,1)`/`nullable=True`; value-set `Check.isin` guards; `strict=False`.
- `tests/test_schemas.py` — 4 DATA-04 tests calling `schema.validate(con.execute("SELECT * FROM <table>").df())`.

## Decisions Made

- **Pandera 0.31.1 namespaced import** — used `import pandera.pandas as pa` and imported `Column`/`Check`/`DataFrameSchema` from `pandera.pandas` (the current API surface), matching RESEARCH Pattern 3.
- **`nullable=True` on AVAILABILITY_YTD is the contract that nulls are legal** — paired with `Check.in_range(0.0, 1.0)` to assert the bound on non-null values without clamping (DATA-03 locked decision: exclude, never impute).
- **`strict=False` on all schemas** — Bronze carries more columns than the contracted ones; only the load-bearing columns are validated, extras pass through.
- **dtype guard via `pd.api.types.is_string_dtype`** — pandas 3.0.3 + DuckDB returns `UNIT_NO` as the new `StringDtype` (not `object`); `is_string_dtype` covers both legacy and modern string representations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] dtype assertion used `== object`, which fails on pandas 3.0 StringDtype**
- **Found during:** Task 2 (test_dtypes RED)
- **Issue:** The first draft asserted `frame["UNIT_NO"].dtype == object`. Under pandas 3.0.3, DuckDB's `.df()` returns `UNIT_NO` as the new `StringDtype(na_value=nan)`, not `object` — so the assertion failed even though the ingest is correct (VARCHAR, zero-padding intact).
- **Fix:** Replaced the equality check with `pd.api.types.is_string_dtype(frame["UNIT_NO"])`, which accepts both legacy `object`-str and modern `StringDtype`.
- **Files modified:** tests/test_schemas.py
- **Verification:** `uv run pytest tests/test_schemas.py -x -q` → 4 passed; `uv run pytest -q` → 15 passed.
- **Committed in:** `f1f3dd5` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug, in the test assertion — not the contract).
**Impact on plan:** None on scope. The fix made the dtype guard correct for the resolved pandas 3.0 stack (consistent with 01-01's note that pandas resolved to 3.0.3).

## Issues Encountered

- The dtype RED above is the only friction; it surfaced the pandas-3.0 `StringDtype` behaviour early, which is useful for downstream plans that assert pandas dtypes.

## User Setup Required

None — in-process pandas/Pandera validation over local Bronze tables. No external services, secrets, or env vars.

## Threat Surface

- T-01-02 (Tampering: out-of-range / unknown-category data entering downstream KPI math) is now mitigated by these schemas — the single applicable ASVS V5 input-validation control for this phase, running as pytest regression guards. No new surface introduced; no threat flags.

## Known Stubs

None — both files are fully wired and exercised against real Bronze data.

## Next Phase Readiness

- DATA-04 is enforced: 0–1 bounds, value sets, and dtypes are green regression guards. Combined with 01-01's row-count (DATA-01) and 209-null/4,405-non-null (DATA-03) guards, ROADMAP success criterion 4 is met.
- `schemas.py` is reusable as the in-test contract for Phase 2 transformed/joined tables.
- Remaining Phase-1 work (plan 01-03): `src/fleet_analytics/profile.py`, `tests/test_profile.py`, and the `deliverables/` DQ report + data dictionary (DATA-02).

## Self-Check: PASSED

- `src/fleet_analytics/schemas.py` and `tests/test_schemas.py` verified present on disk.
- Commits `ed78817` and `f1f3dd5` verified in `git log`.
- `uv run pytest -q` → 15 passed; `uv run pytest tests/test_schemas.py -x -q` → 4 passed.

---
*Phase: 01-ingest-profile-dq-baseline*
*Completed: 2026-06-02*
