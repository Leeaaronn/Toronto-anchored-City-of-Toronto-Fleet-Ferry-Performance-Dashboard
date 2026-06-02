---
phase: 01-ingest-profile-dq-baseline
plan: 01
subsystem: database
tags: [duckdb, pandas, pyarrow, pytest, pandera, uv, csv-ingest, etl, data-quality]

# Dependency graph
requires: []
provides:
  - "uv-managed Python 3.12 project with verified ETL/test stack (duckdb 1.4.4, pandas, pyarrow, pytest, pandera)"
  - "src/fleet_analytics/config.py — exact source filenames, EXPECTED_ROWS, explicit DuckDB type maps"
  - "src/fleet_analytics/ingest.py — ingest_bronze(con) creating 3 typed Bronze tables with fail-fast row-count assert"
  - "tests/conftest.py — session-scoped in-memory DuckDB fixture (con) ingesting Bronze once per session"
  - "DATA-01 row-count guards (4614/2086/272529) and DATA-03 null-preservation guards (209/4405)"
affects:
  - "01-02 (Pandera schemas / value-set + bounds contracts)"
  - "01-03 (profiling + DQ report via SUMMARIZE)"
  - "Phase 2 (UNIT_NO normalization, availability⋈utilization join, derived fields)"

# Tech tracking
tech-stack:
  added:
    - "duckdb 1.4.4 (in-process OLAP, explicit-type CSV ingest)"
    - "pandas 3.0.3, pyarrow 24.0.0"
    - "pytest 9.0.3, pandera 0.31.1 (dev)"
    - "uv 0.10.4 project + uv.lock (reproducible env, Python 3.12 pinned)"
  patterns:
    - "DuckDB read_csv with per-column types override (auto_detect + STRUCT types) — force only load-bearing columns"
    - "Fail-fast row-count assertion in ingest_bronze naming the offending table (T-01-01 mitigation)"
    - "src/ layout with pytest pythonpath=[src]; session-scoped :memory: DuckDB fixture"
    - "Filenames/counts/type maps centralized in config.py — never retyped inline (Pitfall 3)"

key-files:
  created:
    - "pyproject.toml"
    - ".python-version"
    - ".gitignore"
    - "src/fleet_analytics/__init__.py"
    - "src/fleet_analytics/config.py"
    - "src/fleet_analytics/ingest.py"
    - "tests/conftest.py"
    - "tests/test_rowcounts.py"
    - "tests/test_nulls.py"
  modified: []

key-decisions:
  - "Pinned duckdb>=1.4,<1.5 and pandera>=0.26 per RESEARCH registry-drift note (1.5.x not on PyPI; 1.4.4 installed)"
  - "Forced only load-bearing columns via read_csv types= override (rest inferred) — keeps the contract minimal and defensible"
  - "AVAILABILITY_YTD typed DOUBLE, never COALESCE'd — 209 blanks stay genuine NULL (DATA-03 won at ingest)"
  - "zero_ct NOT asserted to 0 — there are 13 legitimate 0.0 availability values; the guard is non_null stays 4405"
  - "In-memory DuckDB for the test fixture (Open Question 1 recommendation) — fast, no stale state"

patterns-established:
  - "Pattern: explicit-type Bronze ingest preserving NULL/zero-padding"
  - "Pattern: fail-fast row-count gate as the first line of CSV-tampering defense"
  - "Pattern: config.py as the single source of truth for filenames/counts/types"

requirements-completed: [DATA-01, DATA-03]

# Metrics
duration: 4min
completed: 2026-06-02
---

# Phase 01 Plan 01: Ingest & DQ Baseline Foundation Summary

**uv-managed Python 3.12 project with explicit-type DuckDB Bronze ingest (4,614 / 2,086 / 272,529) and 11 green pytest guards locking the 209-null AVAILABILITY_YTD rule (denominator 4,405) at ingest time.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-06-02T19:04:27Z
- **Completed:** 2026-06-02T19:08:29Z
- **Tasks:** 3
- **Files modified:** 9 created

## Accomplishments

- Provisioned a reproducible uv project (Python 3.12 pinned, `uv.lock` committed) with the registry-verified stack: duckdb 1.4.4, pandas, pyarrow, pytest, pandera.
- Wrote `ingest_bronze(con)` that lands the three source CSVs into typed Bronze tables with a fail-fast row-count assertion that names the offending table (T-01-01 tampering mitigation).
- Locked DATA-01 (row counts 4,614 / 2,086 / 272,529) and DATA-03 (209 null / 4,405 non-null) as 11 passing pytest guards, with `UNIT_NO` kept VARCHAR (zero-padding preserved) and `AVAILABILITY_YTD` typed DOUBLE so blanks remain genuine SQL NULL.
- Established the test scaffolding (`conftest.py` session-scoped in-memory DuckDB fixture) that all downstream Phase-1 plans run against.

## Task Commits

Each task was committed atomically:

1. **Task 1: Provision uv project, pin Python 3.12, install verified stack** — `fc7553e` (chore)
2. **Task 2: Config + explicit-type Bronze ingest with fail-fast row-count assert (DATA-01)** — `4c314ef` (feat)
3. **Task 3: Null-preservation guards — 209 null / 4,405 non-null / none-became-0 (DATA-03)** — `8051271` (test)

_Note: Tasks 2 and 3 are tdd tasks; RED was observed (ModuleNotFoundError before ingest.py existed) before GREEN. Task 3's guard is structural — the DOUBLE typing in Task 2 already preserves NULLs — so it committed as a `test` gate._

## Files Created/Modified

- `pyproject.toml` — uv project, `requires-python >=3.12,<3.13`, deps, `[tool.pytest.ini_options]` (testpaths, pythonpath=src)
- `.python-version` — pins 3.12
- `.gitignore` — excludes `.venv/`, caches, persisted `*.duckdb`
- `src/fleet_analytics/__init__.py` — package docstring
- `src/fleet_analytics/config.py` — exact filenames (trailing space preserved), `EXPECTED_ROWS`, `AVAIL_TYPES`/`UTIL_TYPES`/`FERRY_TYPES`
- `src/fleet_analytics/ingest.py` — `ingest_bronze(con)`: 3 typed Bronze tables + fail-fast row-count loop
- `tests/conftest.py` — session-scoped in-memory DuckDB `con` fixture
- `tests/test_rowcounts.py` — DATA-01 count assertions + VARCHAR/DOUBLE dtype guards (8 tests)
- `tests/test_nulls.py` — DATA-03 null/non-null/reconciliation guards (3 tests)

## Decisions Made

- **Pinned `duckdb>=1.4,<1.5`, `pandera>=0.26`** per the RESEARCH version-drift note — DuckDB 1.5.x and pandera <0.26 are not installable in this environment; uv resolved duckdb 1.4.4, pandera 0.31.1.
- **`read_csv` with a `types=` STRUCT override (not a full `columns=` map)** — forces only the load-bearing columns (`UNIT_NO`, `AVAILABILITY_YTD`, `Timestamp`, counts) and infers the rest, keeping the contract minimal while still defensible.
- **`zero_ct` deliberately not asserted to 0** — 13 legitimate `0.0` availability values exist; the regression guard is that `non_null` stays 4,405 (a fill would push it toward 4,614).
- **In-memory DuckDB for tests** — per RESEARCH Open Question 1; deterministic and fast (full suite ~0.6s).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `uv init --bare` set `requires-python = ">=3.14"`, blocking the 3.12 pin**
- **Found during:** Task 1 (project provisioning)
- **Issue:** `uv python pin 3.12` failed with "incompatible with the project `requires-python` value of `>=3.14`".
- **Fix:** Edited `pyproject.toml` to `requires-python = ">=3.12,<3.13"`, then re-ran the pin successfully.
- **Files modified:** pyproject.toml
- **Verification:** `.python-version` reads 3.12; `uv run python -c "import duckdb..."` prints 1.4.4.
- **Committed in:** `fc7553e` (Task 1 commit)

**2. [Rule 2 - Missing Critical] Added `.gitignore` and pytest `pythonpath=["src"]`**
- **Found during:** Task 1 / Task 2
- **Issue:** `uv init --bare` created no `.gitignore` (risk of committing `.venv/` and generated `*.duckdb`); and the bare (non-packaged) project left the `src/` layout un-importable, so the test suite hit `ModuleNotFoundError: No module named 'fleet_analytics'`.
- **Fix:** Authored `.gitignore` (`.venv/`, caches, `*.duckdb`); added `pythonpath = ["src"]` to `[tool.pytest.ini_options]`.
- **Files modified:** .gitignore, pyproject.toml
- **Verification:** `.venv/` not staged; `uv run pytest -q` collects and passes (11 tests).
- **Committed in:** `fc7553e` / `4c314ef`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing-critical)
**Impact on plan:** Both were necessary to make the pinned env and src-layout tests runnable. No scope creep — no extra features added.

## Issues Encountered

- **pandas resolved to 3.0.3, not the 2.2.x line CLAUDE.md prefers.** Under Python 3.12 with `pandas>=2.2`, uv resolved 3.0.3. RESEARCH explicitly permits the 3.0.x line ("3.0.x available if desired"), and pandera 0.31.1 + DuckDB interop work against it (full suite green, imports OK). Left as-is rather than force-downgrading; revisit only if a downstream incompatibility surfaces.

## User Setup Required

None — local read-only CSV→DuckDB ingest. No external services, secrets, or env vars.

## Next Phase Readiness

- Bronze ingest + the `con` fixture are ready for 01-02 (Pandera schemas: 0–1 bounds, value sets, dtypes) and 01-03 (profiling/DQ report via `SUMMARIZE`).
- The 4,405 non-null denominator is now asserted from the supplied CSV (closes a STATE.md Phase-1 gate).
- Wave 0 gaps still open for later plans in this phase: `tests/test_schemas.py`, `tests/test_profile.py`, `src/fleet_analytics/schemas.py`, `src/fleet_analytics/profile.py`, and the `deliverables/` DQ report + data dictionary.

## Self-Check: PASSED

- All 9 created files verified present on disk.
- Commits `fc7553e`, `4c314ef`, `8051271` verified in `git log`.
- `uv run pytest -q` → 11 passed; `uv run python -c "import duckdb, pandas, pyarrow, pandera"` → ok.

---
*Phase: 01-ingest-profile-dq-baseline*
*Completed: 2026-06-02*
