# Phase 2: Transform, Model & Join Integrity - Pattern Map

**Mapped:** 2026-06-03
**Files analyzed:** 11 (3 new modules, 1 modified config, 4 new test files, 1 modified conftest, 1 optional schemas extend, 1 reused entry point)
**Analogs found:** 11 / 11 (every new file maps to a real Phase 1 analog — this is a single-codebase data-engineering extension)

All analogs are real Phase 1 files under `src/fleet_analytics/` and `tests/`. Excerpts below are copy-pasteable; the planner should reference the cited file + line range in each plan's `<read_first>`.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/fleet_analytics/transform.py` (NEW) | transform | transform (keyed/derived staging views) | `src/fleet_analytics/ingest.py` | exact (same `CREATE OR REPLACE TABLE AS SELECT` on `con`) |
| `src/fleet_analytics/model.py` (NEW) | model | transform / CRUD (build 5 Gold tables + LEFT JOIN/anti-join) | `src/fleet_analytics/ingest.py` | exact (same per-table builder + fail-fast count loop) |
| `src/fleet_analytics/export.py` (NEW) | export | file-I/O (DuckDB `COPY` to Parquet/CSV) | `src/fleet_analytics/ingest.py` + `config.csv_path` | role-match (DuckDB execute loop over a table list) |
| `src/fleet_analytics/config.py` (MODIFY) | config | constants | `src/fleet_analytics/config.py` (itself — extend) | exact (add `REFERENCE_YEAR`, `GOLD_DIR`, `GOLD_TABLES`) |
| `src/fleet_analytics/schemas.py` (OPTIONAL MODIFY) | schema/contract | validation | `src/fleet_analytics/schemas.py` (itself — extend) | exact (add Gold-tier `DataFrameSchema`s) |
| `tests/conftest.py` (MODIFY) | test fixture | request-response | `tests/conftest.py` (itself — extend) | exact (add `gold` fixture depending on `con`) |
| `tests/test_join_integrity.py` (NEW) | test | request-response | `tests/test_nulls.py` | exact (count helper + reconciliation asserts) |
| `tests/test_derived_fields.py` (NEW) | test | request-response | `tests/test_rowcounts.py` | exact (`@pytest.mark.parametrize` boundary cases) |
| `tests/test_dimensions.py` (NEW) | test | request-response | `tests/test_rowcounts.py` + `tests/test_nulls.py` | exact (count/reconciliation asserts on `con`/`gold`) |
| `tests/test_export.py` (NEW) | test | file-I/O | `tests/test_nulls.py::test_no_null_became_zero` | role-match (second `:memory:` con re-reads exported file) |
| `src/fleet_analytics/ingest.py` (REUSED, unchanged) | — | — | — | dependency, not modified |

---

## Pattern Assignments

### `src/fleet_analytics/transform.py` (transform, keyed/derived staging)

**Analog:** `src/fleet_analytics/ingest.py`

Mirror `ingest._create_bronze` / `ingest_bronze`: a private per-table builder that runs one `CREATE OR REPLACE TABLE … AS SELECT`, plus a `build_all(con)` orchestration entry point that returns `con` for chaining. The RESEARCH `TRY_CAST(UNIT_NO AS BIGINT)` keying and ferry `time_bucket`/derived-field SQL (02-RESEARCH.md Examples 1, 3, 4) go inside these builders.

**Module docstring + import pattern** (ingest.py lines 1-22) — copy the docstring style (purpose, load-bearing columns, locked-decision notes) and the exact imports:
```python
from __future__ import annotations

import duckdb

from fleet_analytics import config
```

**Per-table builder pattern** (ingest.py lines 31-54) — the `CREATE OR REPLACE TABLE AS SELECT` shape on `con`, with parameter binding via `?` for any value (use `config.REFERENCE_YEAR` for `fleet_age`):
```python
def _create_bronze(
    con: duckdb.DuckDBPyConnection,
    table: str,
    filename: str,
    types: dict[str, str],
) -> None:
    path = config.csv_path(filename)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT * FROM read_csv(
            ?, header = true, auto_detect = true, types = {_types_struct(types)}
        )
        """,
        [path],
    )
```

**Orchestration entry point pattern** (ingest.py lines 57-77) — `build_all(con)` calls each builder then returns `con`. RESEARCH Pattern 3 (02-RESEARCH.md lines 199-210) calls `transform.build_all(con)`:
```python
def ingest_bronze(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
    _create_bronze(con, "bronze_availability", config.AVAIL_CSV, config.AVAIL_TYPES)
    _create_bronze(con, "bronze_utilization", config.UTIL_CSV, config.UTIL_TYPES)
    _create_bronze(con, "bronze_ferry", config.FERRY_CSV, config.FERRY_TYPES)
    # ... fail-fast loop ...
    return con
```

**SQL to embed (from 02-RESEARCH.md, live-verified):** `TRY_CAST(UNIT_NO AS BIGINT) AS unit_key_int` (Example 1, lines 282-298); `time_bucket(INTERVAL '15 minutes', "Timestamp") AS ts_15` (Example 3, lines 325-332); season/daypart/day_of_week/is_weekend/sales_redemption_gap CASE block (Example 4, lines 334-350). **Pitfall (02-RESEARCH.md lines 266-268):** use single-quoted `date_part('month', ts)` or scalar `month()/hour()/isodow()/dayname()` — double-quoted `"month"` is a Binder Error.

---

### `src/fleet_analytics/model.py` (model, 5 Gold tables + join)

**Analog:** `src/fleet_analytics/ingest.py` (same per-table builder + fail-fast count-assertion loop)

Build `dim_division`, `fact_vehicle`, `fact_ferry`, `dim_date`, `dim_time` as `CREATE OR REPLACE TABLE`. Add a `build_all(con)` with a fail-fast count loop mirroring `ingest_bronze`'s — assert the locked target counts in code so a regression fails immediately, not only in pytest.

**Fail-fast count-assertion loop pattern** (ingest.py lines 70-75) — reuse verbatim against Gold targets (4614 / 272529 / 21 / 4383 / 96, matched 2080, unmatched 6):
```python
for table, expected in config.EXPECTED_ROWS.items():
    got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    assert got == expected, (
        f"{table}: expected {expected} rows, got {got} "
        "— CSV may have been re-supplied or truncated"
    )
```

**SQL to embed (from 02-RESEARCH.md, all live-verified against real Bronze):**
- `fact_vehicle` availability-anchored `LEFT JOIN` + anti-join — Example 2 (lines 300-323). Anchored on `stg_availability` so the 44 alphanumeric units survive with NULL `unit_key_int`; `fact_vehicle` stays exactly 4,614 rows. **Anti-pattern (lines 213-217):** never `INNER JOIN` and never `WHERE unit_key_int IS NOT NULL` before the fact build.
- `dim_division` normalize + distinct union → 21 rows — Example 5 (lines 352-370): `upper(trim(regexp_replace(col, '\s+', ' ', 'g')))` UNION, `ROW_NUMBER() OVER (ORDER BY division_name)` surrogate. Two role-playing FKs (`owner_division_key` always populated, `using_division_key` nullable).
- `dim_date` gapless 2015→2026 (4,383 rows) + `dim_time` 96 rows — Example 6 (lines 372-396): `generate_series(...)`; natural `DATE` `date_key`, `ROW_NUMBER()` surrogates for division/time.

**Anti-pattern guard (02-RESEARCH.md lines 215, 261-264):** no `COALESCE`/`fillna` on `AVAILABILITY_YTD` anywhere in the Gold build — the 209 NULLs must flow through unchanged (Phase 1 `test_nulls.py` is the regression guard).

---

### `src/fleet_analytics/export.py` (export, Parquet + CSV via COPY)

**Analog:** `src/fleet_analytics/ingest.py` (DuckDB `con.execute` loop) + `config.csv_path` (path-building idiom)

Loop over `config.GOLD_TABLES`, run one `COPY … (FORMAT PARQUET)` and one `COPY … (FORMAT CSV, HEADER)` per table to `config.GOLD_DIR`. RESEARCH provides the loop (02-RESEARCH.md Example 7, lines 398-412):
```python
GOLD_TABLES = ["dim_division", "fact_vehicle", "fact_ferry", "dim_date", "dim_time"]
for t in GOLD_TABLES:
    p = (config.GOLD_DIR / t).as_posix()
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.csv' (FORMAT CSV, HEADER)")
```

**Path-building idiom** (config.py lines 33-35) — keep paths derived from a config constant, never inlined. Table names in the `COPY` come from the internal `GOLD_TABLES` constant (not user input), so f-string interpolation of the table name is safe (Security note, 02-RESEARCH.md lines 528-532). Create `config.GOLD_DIR` before the loop (`GOLD_DIR.mkdir(parents=True, exist_ok=True)`).

---

### `src/fleet_analytics/config.py` (MODIFY — add Gold constants)

**Analog:** `config.py` itself — extend the existing "single source of truth" pattern; never inline values elsewhere.

**Existing constant + path-derivation pattern to mirror** (config.py lines 20-43):
```python
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = Path(os.environ.get("FLEET_DATA_DIR", PROJECT_ROOT / ".planning" / "data"))

EXPECTED_ROWS: dict[str, int] = {
    "bronze_availability": 4614,
    "bronze_utilization": 2086,
    "bronze_ferry": 272529,
}
```

**Additions (D-08, A1, A2 from 02-RESEARCH.md):**
- `REFERENCE_YEAR: int = 2023` — with a docstring comment citing the May 2023 FSD report / audit 2022-2023 benchmark context (D-08 requires documenting the value + rationale).
- `GOLD_DIR: Path = PROJECT_ROOT / "data" / "gold"` (REQUIREMENTS SHIP-01 target).
- `GOLD_TABLES: list[str] = ["dim_division", "fact_vehicle", "fact_ferry", "dim_date", "dim_time"]`.
- Optionally a `GOLD_EXPECTED_ROWS` dict (parallel to `EXPECTED_ROWS`) for the model.py fail-fast loop and `test_dimensions.py` parametrization: `{"dim_division": 21, "fact_vehicle": 4614, "fact_ferry": 272529, "dim_date": 4383, "dim_time": 96}`.

---

### `src/fleet_analytics/schemas.py` (OPTIONAL MODIFY — Gold-tier contracts)

**Analog:** `schemas.py` itself — add new `DataFrameSchema` objects in the established style.

**Pattern to mirror** (schemas.py lines 28-56) — `import pandera.pandas as pa` / `from pandera.pandas import Check, Column, DataFrameSchema`; named value-set constants; `strict=False`; `Check.in_range` / `Check.isin`:
```python
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

availability_schema: DataFrameSchema = DataFrameSchema(
    {
        "UNIT_NO": Column(str, nullable=False),
        "AVAILABILITY_YTD": Column(float, Check.in_range(0.0, 1.0), nullable=True),
        "CATEGORY_CLASS": Column(str, nullable=False),
    },
    strict=False,
    name="availability_schema",
)
```

**Gold contracts (optional, non-gating — 02-RESEARCH.md line 512):** `fleet_age` integer (no lower-bound clamp — range is −3…41, Pitfall 5, lines 270-272); `season ∈ {Winter, Spring, Summer, Fall}`; `daypart ∈ {Morning, Midday, Afternoon/Evening, Night}` via `Check.isin`; `is_weekend` boolean. Reuse the named-value-set-constant idiom (schemas.py lines 35-36).

---

### `tests/conftest.py` (MODIFY — add `gold` fixture)

**Analog:** `conftest.py` itself — the existing session-scoped `con` fixture.

**Existing fixture to extend** (conftest.py lines 14-19):
```python
@pytest.fixture(scope="session")
def con() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    ingest_bronze(connection)
    yield connection
    connection.close()
```

**Add a `gold` fixture depending on `con`** (02-RESEARCH.md Pattern 3, lines 202-210) — builds transform + model on the same connection so Phase-2 tests query real Gold tables without re-ingesting:
```python
@pytest.fixture(scope="session")
def gold(con):
    from fleet_analytics import transform, model
    transform.build_all(con)
    model.build_all(con)
    return con
```

---

### `tests/test_join_integrity.py` (NEW — the hard gate, MODEL-03)

**Analog:** `tests/test_nulls.py` (private count helper + reconciliation asserts)

**Count-helper pattern to mirror** (test_nulls.py lines 18-26) — one SQL query returning all reconciliation figures, destructured per test:
```python
def _counts(con):
    return con.execute(
        """
        SELECT COUNT(*)                           AS total,
               COUNT(AVAILABILITY_YTD)            AS non_null,
               COUNT(*) - COUNT(AVAILABILITY_YTD) AS null_ct
        FROM bronze_availability
        """
    ).fetchone()
```

**Reconciliation assert pattern to mirror** (test_nulls.py lines 41-51) — assert each component AND the sum:
```python
def test_count_reconciliation(con) -> None:
    total, non_null, null_ct = _counts(con)
    assert total == 4614
    assert non_null == 4405
    assert null_ct == 209
    assert null_ct + non_null == total
```

**Tests to write (02-RESEARCH.md lines 479-483, depend on the `gold` fixture):**
- `test_matched_2080` — `SELECT COUNT(*) FROM fact_vehicle WHERE Utilization IS NOT NULL` == 2080.
- `test_unmatched_6` — anti-join count == 6 (the 6 fall outside `fact_vehicle` by design — Pitfall 2, lines 254-258).
- `test_fact_rowcount_4614` — `fact_vehicle` == 4614 (no fan-out, the 44 alnum units survive — Pitfall 1, lines 248-252).
- `test_fact_unique_key` — `COUNT(*) == COUNT(DISTINCT UNIT_NO) == 4614`.
- `test_util_key_not_null` — `COUNT(*) FILTER (WHERE unit_key_int IS NULL) FROM stg_utilization` == 0.
- Reconciliation: 2080 matched + 6 unmatched == 2086.

**Reserved-word caution (02-RESEARCH.md lines 274-276):** use aliases like `in_both` / `null_ct`, never `both` / `nulls` (Parser Error).

---

### `tests/test_derived_fields.py` (NEW — MODEL-01)

**Analog:** `tests/test_rowcounts.py` (`@pytest.mark.parametrize` boundary cases)

**Parametrize pattern to mirror** (test_rowcounts.py lines 13-20):
```python
@pytest.mark.parametrize(
    ("table", "expected"),
    list(EXPECTED_ROWS.items()),
    ids=list(EXPECTED_ROWS.keys()),
)
def test_bronze_rowcount(con, table: str, expected: int) -> None:
    got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    assert got == expected, f"{table}: expected {expected} rows, got {got}"
```

**Boundary cases to parametrize (02-RESEARCH.md lines 495-499):**
- `season`: month 12→Winter, 2→Winter, 3→Spring, 6→Summer, 8→Summer, 9→Fall, 11→Fall.
- `daypart`: hour 5→Night, 6→Morning, 10→Morning, 11→Midday, 14→Midday, 15→Afternoon/Evening, 19→Afternoon/Evening, 20→Night, 23→Night.
- `is_weekend`: known Saturday/Sunday → true; Wednesday → false.
- `fleet_age`: YEAR 2015→8, YEAR 1982→41, YEAR 2026→−3 (assert negatives allowed — do NOT clamp, Pitfall 5).
- `sales_redemption_gap`: signed (Sales − Redemption), e.g. a row → −1 (D-11; do not abs).
- ferry `ts_15`: 0 NaT, 272,529 rows preserved.

---

### `tests/test_dimensions.py` (NEW — MODEL-02)

**Analog:** `tests/test_rowcounts.py` (count asserts) + `tests/test_nulls.py` (reconciliation idiom)

**Tests to write (02-RESEARCH.md lines 488-490, depend on `gold`):**
- `test_dim_date_gapless` — `COUNT(*) == 4383` AND gapless check (`datediff('day', MIN(date_key), MAX(date_key)) + 1 == COUNT(*)`).
- `test_dim_time_96` — `dim_time` == 96 rows.
- `test_dim_division_conformed` — `dim_division` == 21 rows; `division_key` unique (`COUNT(*) == COUNT(DISTINCT division_key)`).

Use the same `con.execute(...).fetchone()[0]` assert idiom as test_rowcounts.py lines 23-35.

---

### `tests/test_export.py` (NEW — MODEL-04)

**Analog:** `tests/test_nulls.py::test_no_null_became_zero` (lines 54-94) — the established "open a second `:memory:` connection, re-read a file, compare to the in-memory table" roundtrip pattern.

**Roundtrip pattern to mirror** (test_nulls.py lines 64-87) — fresh connection in a `try/finally`, re-read the artifact, assert preservation:
```python
raw = duckdb.connect(":memory:")
try:
    raw.execute(
        "CREATE TABLE raw AS SELECT * FROM read_csv("
        "?, header=true, auto_detect=true, types={'AVAILABILITY_YTD': 'VARCHAR'})",
        [config.csv_path(config.AVAIL_CSV)],
    )
    raw_blank = raw.execute(
        "SELECT COUNT(*) FROM raw WHERE AVAILABILITY_YTD IS NULL OR TRIM(AVAILABILITY_YTD) = ''"
    ).fetchone()[0]
finally:
    raw.close()
```

**Tests to write (02-RESEARCH.md lines 491-492, 398-404):**
- `test_parquet_types` — read `data/gold/fact_vehicle.parquet` back; assert `AVAILABILITY_YTD` is DOUBLE with 209 NULLs, `IN_SERV_DT` is DATE, `is_weekend` boolean.
- `test_csv_nulls` — read `data/gold/fact_vehicle.csv` back; assert NULL count == 209 (blanks stay NULL, not 0).
- This test depends on `export.write_gold(con)` having run (or run it in the test against a tmp dir). Use `read_parquet(...)` / `read_csv(...)` on a second connection.

---

## Shared Patterns

### DuckDB SQL-first with `con.execute` on one connection
**Source:** `src/fleet_analytics/ingest.py` lines 43-54 (`con.execute("CREATE OR REPLACE TABLE … AS SELECT …", [params])`)
**Apply to:** `transform.py`, `model.py`, `export.py`, all test files.
Every transformation is one set-based SQL statement on the shared `con`. Bind values with `?` (paths/params); table names come from internal constants only.

### Fail-fast count-assertion loop (in code, not only in tests)
**Source:** `src/fleet_analytics/ingest.py` lines 70-75
**Apply to:** `model.py` `build_all` (assert Gold target counts), mirrored in `tests/test_dimensions.py` and `tests/test_join_integrity.py`.
```python
for table, expected in EXPECTED.items():
    got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    assert got == expected, f"{table}: expected {expected}, got {got}"
```

### Null-preservation discipline (the 209 NULLs survive to Gold)
**Source:** `tests/test_nulls.py` lines 29-51 + `src/fleet_analytics/config.py` lines 48-53 (`AVAILABILITY_YTD: "DOUBLE"`)
**Apply to:** `transform.py` + `model.py` (never `COALESCE`/`fillna` `AVAILABILITY_YTD`); `tests/test_export.py` (re-assert 209 NULLs post-export). The existing `test_nulls.py` stays green as the Bronze regression guard.

### Module docstring convention (purpose + load-bearing columns + locked-decision notes)
**Source:** `src/fleet_analytics/ingest.py` lines 1-16, `config.py` lines 1-13, `schemas.py` lines 1-26
**Apply to:** all three new modules — open with a docstring naming the requirement IDs (MODEL-01…04), the load-bearing columns, and the locked-decision rationale (D-01…D-12).

### Session-scoped fixture reuse (build once, query many)
**Source:** `tests/conftest.py` lines 14-19
**Apply to:** the new `gold` fixture and every Phase-2 test — depend on `gold` (which depends on `con`) so Bronze ingest + Gold build run once per session.

### Imports / package conventions
**Source:** `src/fleet_analytics/ingest.py` lines 18-22, `tests/test_schemas.py` lines 15-23
**Apply to:** all new files. Pattern: `from __future__ import annotations`; `import duckdb`; `from fleet_analytics import config` (or `from fleet_analytics.<module> import <fn>`). Tests import the function/schema under test directly and take `con`/`gold` as a fixture arg. Pandera: `import pandera.pandas as pa` / `from pandera.pandas import Check, Column, DataFrameSchema`.

---

## No Analog Found

None. Every Phase-2 file extends an established Phase-1 pattern — this is a homogeneous DuckDB-SQL-on-`con` data-engineering codebase. The planner should NOT fall back to RESEARCH.md generic patterns for structure; use the cited Phase-1 analogs for module shape, and use RESEARCH.md only for the verified SQL bodies to embed.

---

## Metadata

**Analog search scope:** `src/fleet_analytics/` (ingest.py, config.py, schemas.py, profile.py, __init__.py), `tests/` (conftest.py, test_rowcounts.py, test_nulls.py, test_schemas.py, test_profile.py)
**Files scanned:** 10 source/test files (all read in full — each ≤ 147 lines)
**Pattern extraction date:** 2026-06-03
