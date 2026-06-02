# Stack Research

**Domain:** Small, tested analytics ETL (Python + DuckDB) producing a Power BI–friendly star schema as Parquet/CSV
**Researched:** 2026-06-01
**Confidence:** HIGH

> Scope note: This covers the **data-engineering layer only** — ingest 3 CSVs (4.6k + 2.1k + 272k rows), profile/clean, build a star schema, compute KPIs, export Parquet/CSV. The Power BI report canvas is authored manually in Desktop. `.pbix`/PBIP/TMDL generation is explicitly out of scope and not researched here.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 (3.11+) | Runtime | 3.12 is the stable sweet spot for the 2026 data stack; every library below supports it. Avoid 3.13+ only if a transitive wheel lags — not a concern for this list. DuckDB 1.5 dropped 3.9, so 3.10 is the floor. |
| DuckDB (Python client) | 1.5.x | In-process analytical engine; CSV ingest, SQL transforms, joins, KPI aggregation, Parquet/CSV export | Zero-server OLAP that reads CSV and writes Parquet natively in one process. The entire pipeline (read → model → KPI → export) is expressible in SQL with no external database. Ideal for a single-machine, reproducible, version-controlled assessment. Matches the user's stated portfolio direction. |
| pandas | 2.2.x (3.0 available) | Convenience layer at DuckDB boundaries; `dim_date`/`dim_time` generation; profiling input; test assertions | Stay on the 2.2.x line for maximum library compatibility (pandas 3.0.x exists but is new; pin only if you want it). DuckDB returns/consumes pandas DataFrames seamlessly via `.df()` and `FROM df`. Use pandas where date/calendar generation or row-wise tweaks are clearer than SQL. |
| pyarrow | 16+ (ships current) | Parquet read/write engine; DuckDB↔pandas zero-copy Arrow bridge | The de-facto Parquet engine. pandas `to_parquet` defaults to pyarrow (fastparquet is being retired in pandas 3.1). DuckDB exports Arrow directly. Required for type-preserving Parquet output. |
| pytest | 8.4.x (9.0.x available) | Test runner for schema, row-count, join-integrity, derived-field, and KPI-bounds tests | Standard Python test framework. 8.4.2 is the mature, broadly-compatible choice; 9.0.x is fine if you want latest. Fixtures + `@pytest.mark.parametrize` map cleanly onto "run this DQ rule across N tables / N asset classes." |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pandera | 0.20+ | Declarative schema/DataQuality validation as code — column types, nullability, value ranges (e.g. `AVAILABILITY_YTD ∈ [0,1]`), allowed-value sets (`Utilization ∈ {Underutilized, Not Underutilized}`) | RECOMMENDED for the DQ baseline (Phase 1) and as the in-test contract for transformed tables (Phase 2). Lightweight, type-hint-friendly, runs inside pytest. Encodes the brief's exact business rules (209-null expectation, 0–1 bounds, 21/20 division domains) as executable checks. |
| ydata-profiling **→ fg-data-profiling** | fg-data-profiling 4.19.x | One-line HTML/JSON EDA report (nulls, ranges, outliers, distributions) for the Phase-1 data dictionary + DQ report | OPTIONAL but high-value for the deliverable. NOTE: `ydata-profiling` was renamed to `fg-data-profiling`; the old package is frozen. Use the new name. Generates the profiling artifact (e.g. the 5.8%-vs-14% discrepancy, skewed ferry distribution) cheaply. If you prefer fewer/heavier deps, DuckDB `SUMMARIZE` + Pandera covers the must-haves without it. |
| python-dateutil / pandas date tooling | bundled | Parse `IN_SERV_DT`, ferry `Timestamp`; derive season/daypart/day_of_week/is_weekend | Use `pd.to_datetime` / DuckDB `strptime` / `date_part`. No extra heavy dependency needed. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **uv** | Package manager, virtualenv, lockfile, Python version pinning | RECOMMENDED. Single fast (Rust) tool that replaces pip+venv+pyenv. `uv init`, `uv add duckdb pandas pyarrow`, `uv add --dev pytest pandera`. Produces `uv.lock` for reproducibility — critical for a "reproducible pipeline" claim. ~10x faster CI installs. Works on a bare runner (downloads Python itself). |
| ruff | Lint + format (replaces black + flake8 + isort) | Single Rust tool; fast; `uv add --dev ruff`. Optional but cheap polish for a portfolio repo. |
| GitHub Actions | CI: lint + run pytest on push/PR | OPTIONAL per brief. A minimal `uv sync` → `pytest` workflow is enough; see "What NOT to Use" for why orchestration is overkill. |

## Installation

```bash
# Project scaffold + environment (uv)
uv init fleet-analytics
cd fleet-analytics

# Core ETL stack
uv add duckdb pandas pyarrow

# Data validation (DQ rules as code)
uv add pandera

# Dev / test
uv add --dev pytest ruff

# Optional: one-line profiling report for the DQ deliverable
uv add --dev fg-data-profiling   # NOT the old "ydata-profiling"
```

## DuckDB-vs-pandas guidance (for THIS workload)

Table sizes: availability **4,614**, utilization **2,086**, ferry **272,529** rows. All comfortably in-memory; performance is a non-issue at this scale. The decision is about **clarity, testability, and correctness**, not speed.

**Default to SQL-first in DuckDB. Drop to pandas only at the edges.**

| Task | Recommended | Why |
|------|-------------|-----|
| Read the 3 CSVs | DuckDB `read_csv_auto` / `read_csv` with explicit types | Native, fast, lets you pin column types up front (e.g. force `UNIT_NO` to VARCHAR before normalizing zero-padding). |
| Normalize `UNIT_NO` and join availability ⋈ utilization | DuckDB SQL (`CAST`/`TRIM`/`LPAD` then `JOIN`) | Join-integrity is the flagship "value-added" step (target 2,080/2,086). SQL `JOIN` + a `LEFT JOIN ... WHERE right IS NULL` anti-join makes the match/miss count an explicit, testable query. |
| Derive fleet_age, season, daypart, day_of_week, is_weekend, sales_redemption_gap | DuckDB SQL (`date_part`, `CASE`) — or pandas if a calendar lib is clearer | Set-based derivations are concise and self-documenting in SQL. |
| Build `dim_date` / `dim_time` | pandas (`pd.date_range`) then register into DuckDB | Generating a contiguous calendar/time spine is more idiomatic in pandas; hand the frame to DuckDB with `FROM df`. |
| KPI aggregation (availability by class vs target, underutilization by division, ferry YoY/seasonality, DoW×hour heatmap) | DuckDB SQL `GROUP BY` / window functions | Aggregations + windowing (YoY growth, rankings) are exactly SQL's strength and trivial to assert in tests. |
| Exclude 209 null `AVAILABILITY_YTD` from rate calcs | DuckDB SQL (`AVG` ignores NULL; or explicit `WHERE ... IS NOT NULL`) | Matches the locked "exclude, don't impute" decision; the null count is itself a DQ assertion. |
| Profiling / quick exploratory checks | pandas + fg-data-profiling | EDA artifact generation. |
| Final export to Parquet/CSV | DuckDB `COPY (...) TO 'file.parquet' (FORMAT PARQUET)` | One statement per table; preserves types into Parquet. |

**Rule of thumb:** if it's a transform/join/aggregate, write SQL against DuckDB (testable, declarative, type-safe). If it's calendar generation, a fiddly parse, or feeding a library that wants a DataFrame, use pandas and pass the frame across the (zero-copy Arrow) boundary.

## How Power BI consumes the output (Parquet vs CSV)

VERIFIED: Power BI Desktop has a **native Parquet connector** (Get Data → search "Parquet"). It reads from the **local filesystem**, Azure Blob, and ADLS Gen2 — local files are fully supported, no Azure required.

**Recommendation: export Parquet as the primary handoff; optionally also emit CSV.**

| Format | Pros for THIS project | Cons |
|--------|----------------------|------|
| **Parquet** (primary) | Preserves data types (dates stay dates, `AVAILABILITY_YTD` stays float, booleans stay boolean) → almost no re-typing in Power Query. Columnar + compressed → small files. Clean, professional handoff. | One extra connector click; not human-readable in a text editor. |
| **CSV** (optional secondary) | Human-readable; trivially inspectable; universal. | Everything imports as text → you must re-apply types in Power Query (the `UNIT_NO` zero-padding and date parsing you just fixed can get re-mangled). |

For this data volume (≤272k rows), **load speed is not a deciding factor** — at this scale CSV and Parquet import comparably fast; the benefit of Parquet here is **type fidelity and a tidy deliverable**, not performance. (Parquet's speed/size win only dominates at multi-million-row scale.) Emitting both gives you a type-safe primary path plus a readable fallback for inspection and grading.

Power BI tip to bake into the report spec: keep one Parquet file **per modeled table** (`dim_division`, `fact_vehicle`, `fact_ferry`, `dim_date`, `dim_time`) so each maps 1:1 to a Power BI table; use the Folder connector only if you later split a table across files.

## pytest patterns for THIS pipeline

| Test category (maps to phases) | Pattern | Example |
|--------------|---------|---------|
| Schema / row-count (Phase 1) | Pandera `DataFrameSchema` + a `@pytest.mark.parametrize` over the 3 tables asserting expected columns, dtypes, and exact row counts (4614 / 2086 / 272529) | Catches a re-supplied or truncated CSV immediately. |
| Null / DQ baseline (Phase 1) | Assert `AVAILABILITY_YTD` null count == 209; assert `Utilization` value set == {Underutilized, Not Underutilized}; assert ranges (0–1, YEAR 1982–2026) | Encodes the brief's profiled facts as regression guards. |
| Join integrity (Phase 2 — flagship) | Build the join in a fixture; assert matched count == 2080 and unmatched == 6; assert no `UNIT_NO` duplication inflates `fact_vehicle` (post-join rowcount == 2086 on the utilization side) | The single most important test — protects the value-added measure. |
| Derived-field correctness (Phase 2) | `@pytest.mark.parametrize` cases: known `IN_SERV_DT`/YEAR → expected fleet_age; known timestamps → expected season/daypart/day_of_week/is_weekend; sales/redemption → expected gap | Table-driven, tiny synthetic inputs. |
| KPI bounds / sanity (Phase 3) | Assert availability rates ∈ [0,1]; per-class availability within sane delta of audit benchmarks (95/92/85/88/90); ferry YoY shows the 2020–21 dip; aggregates reconcile to row totals | Guards against silent aggregation errors. |

**Fixtures:** a session-scoped DuckDB `:memory:` connection (or a connection loading tiny `tests/fixtures/*.csv` samples) keeps tests fast and isolated; a fixture returning the joined frame is reused across join + KPI tests. Prefer small synthetic fixtures for logic tests and one "load the real CSVs" smoke test for row-counts.

## Project structure (src layout + uv)

```
fleet-analytics/
  pyproject.toml          # uv-managed; deps + tool config (ruff, pytest)
  uv.lock                 # reproducibility lockfile (commit this)
  README.md
  data/
    raw/                  # 3 source CSVs (gitignore if large/licensed; document pull date)
    processed/            # output Parquet/CSV (dim_*, fact_*)  -> Power BI imports from here
  src/
    fleet_analytics/
      __init__.py
      ingest.py           # read_csv into DuckDB, schema pin
      profile.py          # DQ report / fg-data-profiling
      transform.py        # normalize UNIT_NO, derive fields, join, build star schema
      kpis.py             # KPI/measure SQL
      export.py           # COPY ... TO parquet/csv
      schemas.py          # Pandera schemas (shared by pipeline + tests)
      pipeline.py         # orchestrates end-to-end run
  tests/
    conftest.py           # DuckDB connection + sample-data fixtures
    fixtures/             # tiny synthetic CSVs for logic tests
    test_schema.py
    test_join_integrity.py
    test_derived_fields.py
    test_kpis.py
  docs/
    data_dictionary.md
    kpi_definitions.md
    measures_spec_dax.md  # DAX-ready (hand-authored into Power BI)
  .github/workflows/ci.yml  # optional
```

The **src layout** (package under `src/`) is the modern idiomatic Python default — it forces tests to run against the installed package, catching packaging/import bugs. `uv` supports it out of the box.

## Optional GitHub Actions CI (data pipeline)

Keep it minimal — lint + tests on push/PR. The pipeline is deterministic over committed sample fixtures, so CI needs no database or external data.

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5      # installs uv, handles Python
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run pytest -q
```

`setup-uv` + `uv sync` gives fast, lockfile-pinned installs. Do NOT add scheduled refreshes, data-fetch steps, or deployment — there is nothing to deploy; outputs are static Parquet/CSV the user imports manually.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| DuckDB (SQL-first) | pandas-only pipeline | If the team is uncomfortable with SQL. But you lose declarative, testable joins/aggregations and the clean CSV→Parquet path; not worth it here. |
| DuckDB | Polars | Polars is excellent and faster than pandas, but DuckDB already covers SQL transforms + Parquet I/O in one engine and matches the chosen direction. Polars adds value mainly for very large or streaming data — not this scale. |
| Pandera | Great Expectations | GE suits large production pipelines with data docs/alerting. Heavyweight and slower for an in-memory, code-tested small project; Pandera is the lighter, code-first fit. |
| uv | Poetry | Poetry remains strong for libraries published to PyPI. This is an application/pipeline, not a published library — uv's speed and all-in-one simplicity win. |
| uv | pip + venv + requirements.txt | Acceptable fallback if uv can't be installed, but you lose a real lockfile (reproducibility) and speed. |
| fg-data-profiling | DuckDB `SUMMARIZE` + Pandera only | If you want fewer/lighter deps, `SUMMARIZE` + Pandera covers the must-have DQ facts; skip the profiling HTML. |
| Parquet output | CSV-only output | Only if a grader explicitly needs to open files in a text editor and you can't ship both. Prefer shipping both. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Airflow / Prefect / Dagster | Orchestration frameworks are massive overkill for a 3-CSV, single-run, single-machine pipeline. Adds servers, schedulers, and ops burden with zero benefit. | A plain `pipeline.py` (function calls) run via `uv run python -m fleet_analytics.pipeline`. |
| A server database (Postgres/MySQL) | Requires standing up and connecting to a server; DuckDB is in-process and file-based. | DuckDB (in-process / `:memory:` or a local `.duckdb` file). |
| `pandas-profiling` (old name) | Renamed; the old package is frozen and unmaintained. | `fg-data-profiling` (formerly ydata-profiling). |
| fastparquet | Being retired; pandas 3.1 deprecates the `fastparquet`/`auto` engine options. | pyarrow (the default Parquet engine). |
| Imputing the 209 nulls | Locked decision — imputation distorts audit-benchmarked rates. | Exclude from rate calcs and assert the null count in a DQ test. |
| Generating `.pbix`/PBIP/TMDL | Out of scope; report canvas authored manually. | Hand the user clean Parquet + a DAX-ready measures spec doc. |
| dbt-duckdb | Adds a modeling framework + project conventions; for ~5 models authored once, plain SQL files / DuckDB scripts are simpler and just as testable. | DuckDB SQL in `transform.py`/`kpis.py` + pytest. (Reconsider dbt only if the model set grows substantially.) |

## Stack Patterns by Variant

**If you want the leanest possible dependency set:**
- DuckDB + pyarrow + pytest + uv only; skip pandas (use DuckDB for `dim_date` via `range`/`generate_series`) and skip fg-data-profiling (use `SUMMARIZE`).
- Because: fewer deps = faster, more reproducible, easier to defend. Trade-off: calendar generation and profiling are slightly more verbose in pure SQL.

**If the profiling/DQ deliverable is graded heavily (likely here):**
- Add Pandera (rules-as-code) + fg-data-profiling (HTML/JSON artifact).
- Because: produces a polished, citable data-quality report and machine-checkable contracts that directly satisfy the Phase-1 deliverable.

**If CI is desired:**
- Add the minimal GitHub Actions workflow above (lint + pytest over committed fixtures).
- Because: a green badge + passing join-integrity tests is strong evidence of a "tested, reproducible" pipeline for the panel interview.

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| DuckDB 1.5.x | Python 3.10+ | 1.5.0 dropped Python 3.9; use 3.11/3.12. |
| pandas 2.2.x | pyarrow 16+ | pyarrow is the default Parquet engine; fastparquet deprecated in pandas 3.1. Pin pandas 2.2.x for broadest library compat (3.0.x available if desired). |
| Pandera 0.20+ | pandas 2.2.x | Validate pandas frames; pass DuckDB results via `.df()` then validate. |
| pytest 8.4.x | Python 3.10+ | 9.0.x available; 8.4.2 is the conservative choice. |
| fg-data-profiling 4.19.x | pandas 2.x | Import name changes to `data_profiling`; pulls heavier sub-deps (matplotlib etc.) — keep it dev-only. |
| uv (latest) | any | Standalone binary; can provision Python itself on CI. Commit `uv.lock`. |

## Sources

- [duckdb · PyPI](https://pypi.org/project/duckdb/) and [duckdb-python releases](https://github.com/duckdb/duckdb-python/releases) — DuckDB 1.5.0 (Mar 2026), Python 3.10 floor. HIGH.
- [Power Query Parquet connector — Microsoft Learn](https://learn.microsoft.com/en-us/power-query/connectors/parquet) — native Parquet connector, supports local filesystem + Azure. HIGH.
- [Benchmarking Power BI import speed for local data sources — SQLGene](https://www.sqlgene.com/2024/11/28/benchmarking-power-bi-import-speed-for-local-data-sources/) and [Parquet and CSV in Power BI — Datalineo](https://www.datalineo.com/post/parquet-and-csv-querying-processing-in-power-bi) — Parquet's edge is type fidelity/size; speed parity at low row counts. MEDIUM.
- [pandas.DataFrame.to_parquet — pandas docs](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html) — pyarrow default engine; fastparquet deprecated in 3.1; pandas 3.0.3 current. HIGH.
- [ydata-profiling / fg-data-profiling GitHub](https://github.com/ydataai/ydata-profiling) — rename to fg-data-profiling; old package frozen; v4.19.1 (Apr 2026). HIGH.
- [The data validation landscape in 2025 — aeturrell](https://aeturrell.com/blog/posts/the-data-validation-landscape-in-2025/) and [Pandera vs Great Expectations — endjin](https://endjin.com/blog/a-look-into-pandera-and-great-expectations-for-data-validation) — Pandera is the lightweight code-first choice. MEDIUM.
- [Best Python Package Managers 2026 — scopir](https://scopir.com/posts/best-python-package-managers-2026/) and [uv vs pip vs Poetry — danilchenko.dev](https://www.danilchenko.dev/posts/uv-vs-pip-vs-poetry/) — uv recommended for new app/pipeline projects. MEDIUM.
- [pytest · PyPI](https://pypi.org/project/pytest/) + [pytest releases](https://github.com/pytest-dev/pytest/releases) — 8.4.2 (Sep 2025), 9.0.x current. HIGH.
- [pytest parametrize — official docs](https://docs.pytest.org/en/stable/how-to/parametrize.html) — fixture/parametrize patterns for data tests. HIGH.

---
*Stack research for: small tested Python+DuckDB analytics ETL → Power BI Parquet/CSV*
*Researched: 2026-06-01*
