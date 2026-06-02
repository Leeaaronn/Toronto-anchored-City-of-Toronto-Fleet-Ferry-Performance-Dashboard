# Phase 1: Ingest, Profile & DQ Baseline - Research

**Researched:** 2026-06-02
**Domain:** Data ingestion, profiling, and data-quality contracts (DuckDB + Pandera + pytest, single-machine reproducible pipeline)
**Confidence:** HIGH (all numeric DQ facts verified directly against the source CSVs in this session)

## Summary

Phase 1 lands three City of Toronto CSVs into typed DuckDB Bronze tables, documents every data-quality fact as a stated assumption, and freezes those facts as executable Pandera regression guards. There is **no CONTEXT.md** for this phase — the constraints below are lifted from `CLAUDE.md` (PROJECT + STACK + Constraints) and the ROADMAP/REQUIREMENTS, which act as locked decisions.

The single most important property of this phase: **the data shape is verified, not assumed.** I loaded all three CSVs through DuckDB during this research and confirmed every headline number the planner needs to encode as an assertion. Row counts are exact (4,614 / 2,086 / 272,529 data rows). The 209-null / 4,405-non-null split on `AVAILABILITY_YTD` is confirmed, and `AVAILABILITY_YTD` already sits in `[0.0, 1.0]`. The "exclude, never impute" rule is a locked decision; the null count is itself a DQ assertion.

**Primary recommendation:** Build Bronze ingestion as **DuckDB `read_csv` with an explicit column-type map** (force `UNIT_NO` to `VARCHAR` to preserve zero-padding; let `AVAILABILITY_YTD` be `DOUBLE` so blanks become genuine SQL `NULL`, never `0`). Encode the four DQ contracts (row count, 209 null, 4,405 non-null, 0–1 bounds) as Pandera schemas run inside pytest. Generate the DQ-report numbers from DuckDB `SUMMARIZE` + targeted aggregation queries (deterministic, citable). Treat the heavy HTML profiler as **optional and dev-only** — it is not installable on the local Python and is not on the phase's critical path.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CSV → typed Bronze table | DuckDB (in-process engine) | — | Native `read_csv` with explicit types; one statement per source |
| Type coercion / NULL preservation | DuckDB (ingest-time column types) | pandas (`.df()` at test boundary) | Column-type map decides whether a blank becomes NULL or 0 — this is where the 209-null rule lives |
| DQ fact computation (counts, ranges, skew) | DuckDB SQL (`SUMMARIZE`, `COUNT`, `MEDIAN`, `MAX`) | pandas for any row-wise framing | Deterministic, re-runnable, citable in the DQ report |
| DQ contract enforcement (regression guards) | Pandera schema + pytest | — | Declarative column types / nullability / value ranges as code |
| DQ report + data dictionary (deliverable docs) | Markdown authored from SQL outputs | ydata-profiling (optional HTML/JSON) | Numbers come from SQL; profiler is decorative, not load-bearing |
| Profiling artifact (HTML/JSON EDA) | ydata-profiling (OPTIONAL, dev-only) | DuckDB `SUMMARIZE` (fallback) | Heavy deps; not installable on local Py 3.9 — see Environment Availability |

<user_constraints>
## User Constraints (from CLAUDE.md — no CONTEXT.md exists for this phase)

### Locked Decisions (from PROJECT + Constraints)
- **Scope split**: GSD owns the data-engineering layer only (ingest, clean, profile, model, KPI logic). The Power BI report canvas is authored manually. Do **not** generate `.pbix` / PBIP / TMDL.
- **Tech stack**: Python + DuckDB for ETL, pandas where convenient, pytest for transformation/join-integrity tests. Output clean Parquet/CSV for Power BI import.
- **Data fidelity (Phase-1 critical)**: The **209 `AVAILABILITY_YTD` nulls are excluded, never imputed**; underutilization is **pre-classified, not recomputed**; thresholds are **cited from the audit, not recalculated**.
- **Sourcing**: Cite City of Toronto Open Data, the May 2023 FSD General Government Committee report, and the AG Operational Review (2019.AU2.2 / 2019.AU2.3); Open Government Licence – Toronto.
- **Assessment stakes**: Output must be defensible and audit-grounded (70% pass → panel interview).

### Claude's Discretion
- Whether to use DuckDB `SUMMARIZE`-only vs. add the optional `ydata-profiling` HTML report for the DQ deliverable (the STACK notes both variants).
- Package manager: `uv` recommended; `pip + venv` is an acceptable fallback.
- `ruff` lint/format is optional polish.

### Deferred Ideas (OUT OF SCOPE for Phase 1)
- Imputing the 209 nulls (explicitly excluded — distorts audit-benchmarked rates).
- Recomputing underutilization classification or km/engine-hour telematics logic.
- Joining ferry into the fleet star schema (different grain).
- Generating any Power BI canvas / PBIP / TMDL artifact.
- The availability⋈utilization join itself (that is Phase 2, not Phase 1).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Three source CSVs load into DuckDB Bronze tables with explicit types and fail-fast row-count assertions (4,614 / 2,086 / 272,529) | Row counts verified directly (see Verified Data Facts). Ingest pattern: `read_csv` with `columns=` type map; assert `SELECT COUNT(*)` per table. |
| DATA-02 | Data dictionary + DQ report documenting nulls, ranges, outliers, ferry skew (median 12 / max 7,229), retired-dataset pull-date caveat, and the 5.8% vs 14% underutilization discrepancy as a stated insight | All numbers verified: ferry Sales median 12 / max 7,229; underutilized 120/2,086 = 5.75% ≈ 5.8%. Generate via DuckDB `SUMMARIZE` + targeted queries. |
| DATA-03 | 209 null `AVAILABILITY_YTD` preserved as genuine NULL (never 0), excluded from rate calcs (denominator 4,405), flagged as DQ gap with no imputation | Verified: 4,614 total, 4,405 non-null, 209 null. Ingest must type the column as `DOUBLE` so blanks → SQL NULL. "Zero originally-null-became-0" guard described in Validation Architecture. |
| DATA-04 | Pandera schemas encode row-count, 209-null, 4,405-non-null, and 0–1 availability-bounds expectations as executable regression guards | Pandera `DataFrameSchema` with `Column(float, Check.in_range(0,1), nullable=True)` + statistical checks; run in pytest. All target values confirmed. |
</phase_requirements>

## Verified Data Facts (loaded from the actual CSVs this session)

> These are `[VERIFIED: DuckDB read of source CSV, 2026-06-02]` unless noted. The planner should hard-code these as assertion targets.

**File names (note the exact spelling — there is a trailing space in the availability filename):**
- `City Vehicle Availability .csv` (trailing space before `.csv`)
- `Light duty city vehicle utilization data.csv`
- `Toronto Island Ferry Ticket Counts.csv`

| Source | Bronze table | Data rows (excl. header) | Verified |
|--------|--------------|--------------------------|----------|
| Availability | `bronze_availability` | **4,614** | ✓ |
| Utilization | `bronze_utilization` | **2,086** | ✓ |
| Ferry | `bronze_ferry` | **272,529** | ✓ |

**Availability (`City Vehicle Availability .csv`)** — columns: `_id, UNIT_NO, YEAR, MAKE, MODEL, CATEGORY, CAT_DESC, UNIT_TYPE, CATEGORY_CLASS, CAT_GRP, IN_SERV_DT, STATUS_DESC, CLASS2, HIGH_PRIORITY, OWNER_DIVISION, REF_DIVISION, SEASONAL, AVAILABILITY_YTD`
- `AVAILABILITY_YTD`: total 4,614 / **non-null 4,405 / null 209** / min **0.0** / max **1.0** ✓ (already in [0,1] — no clamping needed, just assert bounds)
- `UNIT_NO`: auto-types as **VARCHAR**; lengths 5–9 chars; **zero-padded** (e.g. `001052`). Preserve as string in Bronze — integer normalization is a **Phase 2** task, not Phase 1.
- `YEAR` range: **1982 → 2026**
- Distinct `OWNER_DIVISION`: **21**; distinct `CATEGORY_CLASS`: **19**; distinct `STATUS_DESC`: **4**
- `IN_SERV_DT` parses as ISO date (`2014-10-28`)

**Utilization (`Light duty city vehicle utilization data.csv`)** — columns: `_id, UNIT_NO, YEAR, MAKE, MODEL, Specialized units, REF_USING_DIV, Utilization`
- `Utilization` value set: **`Underutilized` (120)`, `Not Underutilized` (1,966)`** → 120/2,086 = **5.75% ≈ 5.8%** (this is the figure that contrasts with the audit's ~14%)
- `Specialized units` value set: **`Yes` (825) / `No` (1,261)**
- `UNIT_NO`: VARCHAR, zero-padded (same normalization concern as availability)

**Ferry (`Toronto Island Ferry Ticket Counts.csv`)** — columns: `_id, Timestamp, Redemption Count, Sales Count`
- Rows: 272,529, **zero nulls** in any column
- `Timestamp`: auto-types as **TIMESTAMP**, range **2015-05-01 13:30 → 2026-06-01 22:30**; all 12 calendar years 2015–2026 present
- `Sales Count`: **median 12 / max 7,229** ✓ (matches brief's "median 12 / max 7,229")
- `Redemption Count`: median 11 / max 7,216
- Heavy right skew (median ~12 vs max ~7,229) — the documented "ferry skew" outlier story; **do not treat the max as an error** (peak ferry windows). 15-minute slot rounding is a Phase 2 task.

**`[ASSUMED]` caveats to confirm in the DQ report (see Assumptions Log):** the "retired-dataset pull-date caveat" (availability is a snapshot pull, not live) and the exact audit benchmark of ~14% underutilization are narrative claims sourced from the brief, not derivable from the CSVs — they must be cited, not computed.

## Standard Stack

### Core
| Library | Version (verify) | Purpose | Why Standard |
|---------|------------------|---------|--------------|
| DuckDB (python) | **1.4.4** is current on PyPI for this env | CSV ingest with explicit types, SQL profiling/aggregation, Bronze tables | In-process OLAP, reads CSV natively, one-process reproducible pipeline `[VERIFIED: pip index versions duckdb → 1.4.4 latest; locally installed 1.4.4]` |
| pandas | **2.3.3** installed | Test-boundary frames (`.df()`), `dim_*` generation later, Pandera input | DuckDB ↔ pandas interop via `.df()` / `FROM df` `[VERIFIED: import pandas → 2.3.3]` |
| pyarrow | **21.0.0** installed | Parquet engine (used heavily in Phase 2; not Phase 1 critical) | De-facto Parquet engine `[VERIFIED: import pyarrow → 21.0.0]` |
| pytest | 8.x (9.0 available) | Runs Pandera + count/null assertions | Standard runner; parametrize over the 3 tables `[ASSUMED — not yet installed locally]` |
| Pandera | **0.26.1** current (Py 3.9 floor) | Declarative DQ contracts: types, nullability, 0–1 range, value sets, row-count via stats | Lightweight code-first validation `[VERIFIED: pip index versions pandera → 0.26.1 latest]` |

> **Version-drift note for the planner:** `CLAUDE.md`/STACK.md recommends "DuckDB 1.5.x" and "Pandera 0.20+". The registry today shows **DuckDB 1.4.4** as the latest installable release (1.5.x is **not** on PyPI for this environment) and **Pandera 0.26.1**. Pin to what the registry actually serves: `duckdb>=1.4,<1.5`, `pandera>=0.26`. `[VERIFIED: pip index versions, 2026-06-02]`

### Supporting / Optional
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ydata-profiling | **4.17.0** (latest installable on Py 3.9) | One-line HTML/JSON EDA report for the DQ-report deliverable | OPTIONAL, dev-only. STACK.md calls for `fg-data-profiling`, which is **NOT installable here** (requires Python ≥3.10). See Environment Availability. |
| uv | 0.10.4 installed | Env + lockfile + Python pinning | RECOMMENDED for the reproducibility claim `[VERIFIED: uv --version → 0.10.4]` |
| ruff | latest | Lint/format polish | Optional |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| DuckDB `SUMMARIZE` + Pandera (must-haves) | ydata-profiling HTML report | Profiler is a nicer artifact but heavy and not installable on local Py 3.9; SUMMARIZE+Pandera fully satisfies DATA-02/03/04 |
| Pandera | Great Expectations | GE is heavyweight; Pandera is the code-first fit for an in-memory tested project |
| DuckDB-typed ingest | pandas `read_csv` | pandas silently coerces blank floats to `NaN` and can stringify zero-padding inconsistently; DuckDB explicit `columns=` map is more defensible for the 209-null and zero-pad rules |

**Installation (pin to verified registry versions):**
```bash
uv add "duckdb>=1.4,<1.5" "pandas>=2.2" "pyarrow>=16"
uv add --dev pytest "pandera>=0.26"
# OPTIONAL profiling artifact (requires Python >=3.10 — see Environment Availability):
# uv add --dev "ydata-profiling>=4.17"
```

## Package Legitimacy Audit

slopcheck 0.6.1 ran successfully against all candidate packages.

| Package | Registry | Age | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-------------|-----------|-------------|
| duckdb | PyPI | mature (1.4.4 current) | github.com/duckdb/duckdb | [OK] | Approved |
| pandas | PyPI | mature | github.com/pandas-dev/pandas | [OK] | Approved |
| pyarrow | PyPI | mature | github.com/apache/arrow | [OK] | Approved |
| pytest | PyPI | mature | github.com/pytest-dev/pytest | [OK] | Approved |
| pandera | PyPI | mature (0.26.1) | github.com/unionai-oss/pandera | [OK] | Approved |
| ydata-profiling | PyPI | mature (4.17.0) | github.com/ydataai/ydata-profiling | [OK] | Approved (optional) |
| fg-data-profiling | PyPI | **41 days old** | (rename fork) | [OK but flagged] | **Avoid** — not installable on Py 3.9 (requires ≥3.10) AND only 41 days old. Use `ydata-profiling` instead. |
| uv | PyPI | mature | github.com/astral-sh/uv | [OK] | Approved |
| ruff | PyPI | mature | github.com/astral-sh/ruff | [OK] | Approved (optional) |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged:** `fg-data-profiling` — slopcheck rates [OK] but it is only 41 days old and **does not install on the local Python 3.9 env**. STACK.md's claim that `ydata-profiling` is "frozen/renamed" is contradicted by the registry: `ydata-profiling` 4.17.0 is current and actively published. Recommendation: if a profiler is used at all, use **`ydata-profiling`**, not `fg-data-profiling`. Since profiling is OPTIONAL, the safest path is to skip it and derive DQ numbers from DuckDB `SUMMARIZE`.

## Architecture Patterns

### System Architecture Diagram

```
  3 source CSVs (repo root, exact filenames incl. trailing space)
        │
        ▼
  [ ingest.py ]  DuckDB read_csv(columns={explicit type map})
        │            • UNIT_NO -> VARCHAR (preserve zero-pad)
        │            • AVAILABILITY_YTD -> DOUBLE (blank -> NULL, never 0)
        │            • Timestamp -> TIMESTAMP (tz-naive)
        ▼
  Bronze tables in a DuckDB file (or :memory:):
   bronze_availability (4,614)  bronze_utilization (2,086)  bronze_ferry (272,529)
        │                              │                          │
        ├──────────────┬──────────────┴──────────────┬───────────┘
        ▼              ▼                              ▼
  [ profile.py ]   [ dq_checks (Pandera) ]      DQ report numbers
  SUMMARIZE +      row-count / 209-null /        (nulls, ranges, skew,
  targeted SQL     4,405-non-null / 0–1 bounds   5.8% vs 14%)
        │              │                              │
        ▼              ▼                              ▼
  data_dictionary.md   pytest (regression guards)   dq_report.md
                           │
                           ▼
                   GREEN gate -> Phase 2 may begin
```

### Recommended Project Structure (src layout)
```
src/fleet_analytics/
├── __init__.py
├── config.py          # source filenames (with trailing space), expected row counts, type maps
├── ingest.py          # read_csv(columns=...) -> Bronze tables; fail-fast row-count assert
├── profile.py         # SUMMARIZE + targeted DQ queries -> dict of facts for the report
└── schemas.py         # Pandera DataFrameSchemas (the DQ contracts)
tests/
├── conftest.py        # fixtures: connect DuckDB, ingest Bronze once per session
├── test_rowcounts.py  # parametrized over 3 tables: 4614 / 2086 / 272529
├── test_nulls.py      # AVAILABILITY_YTD null==209, non-null==4405, zero-became-0==0
└── test_schemas.py    # run Pandera schemas; assert value sets and 0–1 bounds
deliverables/
├── data_dictionary.md
└── dq_report.md
data/
├── source/            # (or repo root) the 3 CSVs
└── bronze/            # optional persisted .duckdb
```

### Pattern 1: Explicit-type CSV ingest (the NULL-preservation guarantee)
**What:** Force column types at read time so blanks in `AVAILABILITY_YTD` become SQL `NULL`, and `UNIT_NO` keeps its zero-padding.
**When to use:** Always, for Bronze ingest — this is where DATA-03 is won or lost.
```python
# Source: DuckDB CSV import docs (https://duckdb.org/docs/data/csv/overview)
AVAIL_TYPES = {
    "UNIT_NO": "VARCHAR",          # preserve zero-padding (e.g. '001052')
    "AVAILABILITY_YTD": "DOUBLE",  # blank cell -> NULL, NEVER 0
    "YEAR": "INTEGER",
    "IN_SERV_DT": "DATE",
}
con.execute("""
    CREATE TABLE bronze_availability AS
    SELECT * FROM read_csv('City Vehicle Availability .csv', header=true, columns=$types)
""", {"types": AVAIL_TYPES})
```

### Pattern 2: Fail-fast row-count assertion at ingest
```python
EXPECTED = {"bronze_availability": 4614, "bronze_utilization": 2086, "bronze_ferry": 272529}
for tbl, n in EXPECTED.items():
    got = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    assert got == n, f"{tbl}: expected {n} rows, got {got} — CSV may have been re-supplied/truncated"
```

### Pattern 3: Pandera DQ contract
```python
# Source: Pandera docs (https://pandera.readthedocs.io/)
import pandera.pandas as pa
from pandera import Column, Check, DataFrameSchema

availability_schema = DataFrameSchema(
    {
        "UNIT_NO": Column(str, nullable=False),
        "AVAILABILITY_YTD": Column(
            float, Check.in_range(0.0, 1.0), nullable=True   # 209 nulls are LEGAL
        ),
        "CATEGORY_CLASS": Column(str, nullable=False),
    },
    strict=False,
)
# Row-count + null-count are asserted in pytest (statistical, not per-row) — see Validation Architecture.
```

### Anti-Patterns to Avoid
- **`pd.read_csv` with default float coercion then `.fillna(0)`** — silently destroys the 209-null DQ signal. Never fill.
- **Casting `UNIT_NO` to INT during ingest** — drops zero-padding and pre-empts the Phase-2 normalization decision. Keep VARCHAR in Bronze.
- **`read_csv_auto` for the typed Bronze tables** — auto-inference is fine for exploration but the type map must be explicit so the contract is defensible.
- **Treating ferry max 7,229 as a data error** — it is a real peak window; document as skew, do not clip.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Column-type / nullability / range validation | Custom `assert` ladders per column | Pandera `DataFrameSchema` | Declarative, reusable, produces readable failure reports; encodes the contract once |
| CSV parsing with quoted commas (e.g. `"ENVIRONMENT, CLIMATE & FORESTR"`) | Hand-split on commas | DuckDB `read_csv` | RFC-4180 quoting handled; the OWNER_DIVISION field contains embedded commas |
| Numeric summaries (nulls, min/max, median, distinct) | Manual aggregation loops | DuckDB `SUMMARIZE` + targeted SQL | One statement, deterministic, citable in the DQ report |
| Reproducible env | `requirements.txt` by hand | `uv` + `uv.lock` | Lockfile is the evidence behind the "reproducible pipeline" claim |

**Key insight:** Every DQ fact in this phase must be both *documented* (DQ report) and *enforced* (Pandera/pytest). Hand-rolled checks tend to document OR enforce, not both — Pandera does both from one definition.

## Common Pitfalls

### Pitfall 1: Blank availability cells silently become 0
**What goes wrong:** A pandas-first ingest or a `COALESCE(...,0)` turns the 209 genuine nulls into zeros, inflating the denominator to 4,614 and dragging down every availability rate.
**Why it happens:** Default float handling + well-meaning "clean the nulls" instinct.
**How to avoid:** Type `AVAILABILITY_YTD` as `DOUBLE` at ingest, never fill, and add the explicit "zero originally-null-became-0 == 0" guard (Validation Architecture).
**Warning signs:** non-null count reads 4,614 instead of 4,405; min availability is exactly 0.0 with a spike of zeros.

### Pitfall 2: UNIT_NO zero-padding lost
**What goes wrong:** `001052` becomes `1052`; later the Phase-2 join silently mismatches.
**Why it happens:** Integer inference at read time.
**How to avoid:** Keep `UNIT_NO` VARCHAR in Bronze; normalization happens in Phase 2 with its own integrity test.
**Warning signs:** `MIN(LENGTH(UNIT_NO))` drops; leading-zero units missing.

### Pitfall 3: Exact source filename (trailing space)
**What goes wrong:** `FileNotFoundError` because the availability CSV is literally `City Vehicle Availability .csv` (space before `.csv`).
**How to avoid:** Centralize filenames in `config.py`; never retype them inline.

### Pitfall 4: Ferry timestamp timezone drift
**What goes wrong:** Parsing as tz-aware shifts hour-of-day, corrupting the future daypart/heatmap (Phase 2/3).
**How to avoid:** Parse tz-naive at ingest (DuckDB TIMESTAMP is tz-naive by default). Phase 1 only needs to store it correctly.

## Code Examples

### DuckDB SUMMARIZE for the DQ report
```python
# Source: DuckDB docs (https://duckdb.org/docs/sql/statements/summarize)
con.execute("SUMMARIZE bronze_availability").df()   # null_percentage, min, max, q50, distinct per column
```

### The three null assertions (the heart of DATA-03)
```python
row = con.execute("""
  SELECT COUNT(*)                                AS total,
         COUNT(AVAILABILITY_YTD)                 AS non_null,
         COUNT(*) - COUNT(AVAILABILITY_YTD)      AS null_ct,
         COUNT(*) FILTER (WHERE AVAILABILITY_YTD = 0) AS zero_ct
  FROM bronze_availability
""").fetchone()
assert row == (4614, 4405, 209, /* zero_ct: documented, not asserted to 0 */)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pandas-profiling` | `ydata-profiling` 4.17.0 | renamed years ago | Use `ydata-profiling` if profiling at all |
| STACK.md's `fg-data-profiling` | `ydata-profiling` 4.17.0 | — | `fg-data-profiling` is 41 days old and NOT installable on Py 3.9; ydata-profiling is the maintained, installable package |
| DuckDB 1.5.x (STACK claim) | DuckDB **1.4.4** (registry reality) | — | Pin `duckdb>=1.4,<1.5`; 1.5.x is not on PyPI for this env |
| `fastparquet` engine | pyarrow (default) | pandas 3.1 deprecation | Phase-2 concern; pyarrow 21.0.0 already installed |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The "retired-dataset pull-date caveat" — availability is a point-in-time snapshot, not live | DATA-02 / DQ report | Narrative; must be cited from the brief, not computed. Low risk if framed as a stated assumption. |
| A2 | The ~14% audit underutilization benchmark (vs computed 5.8%) | DATA-02 | Sourced from the AG report, not the CSV. Must carry an inline citation; do not present as derived. |
| A3 | pytest will install cleanly (`pytest`, `pandera>=0.26`) on this env | Standard Stack | Both verified on PyPI; pandera 0.26.1 installs on Py 3.9. Low risk. |
| A4 | DuckDB `read_csv(columns=...)` with the trailing-space filename works as written | Patterns | Filenames verified to exist; DuckDB read verified this session. Low risk. |

## Open Questions

1. **Should a `.duckdb` file be persisted or run in `:memory:` for Phase 1?**
   - Known: either works; Bronze is regenerated from CSV deterministically.
   - Recommendation: ingest into `:memory:` for tests (fast, no stale state) and optionally persist a `data/bronze/*.duckdb` for inspection. Defer the persisted-file decision to the planner.

2. **Whether to ship the optional ydata-profiling HTML at all.**
   - Recommendation: skip it for Phase 1 (heavy, not installable on local Py 3.9). Derive all DQ-report numbers from `SUMMARIZE` + targeted SQL. Revisit only if a richer artifact is explicitly wanted.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | runtime | ✓ | **3.9.13** (STACK targets 3.12) | works for duckdb 1.4 / pandera 0.26 |
| uv | env + lockfile | ✓ | 0.10.4 | pip + venv |
| DuckDB (py) | ingest, profiling | ✓ | 1.4.4 installed | — |
| pandas | test boundary | ✓ | 2.3.3 | — |
| pyarrow | Parquet (Phase 2) | ✓ | 21.0.0 | — |
| pytest | DQ tests | ✗ (not yet installed) | — | `uv add --dev pytest` (verified on PyPI) |
| pandera | DQ contracts | ✗ (not yet installed) | 0.26.1 available | `uv add --dev "pandera>=0.26"` |
| ydata-profiling | optional HTML EDA | ⚠ installable (4.17.0) | — | DuckDB `SUMMARIZE` (preferred) |
| fg-data-profiling | (STACK suggestion) | ✗ | requires Py ≥3.10 | use `ydata-profiling` or skip |
| 3 source CSVs | ingest | ✓ | present at repo root | — |

**Missing dependencies with no fallback:** none.
**Missing with fallback:** `pytest` and `pandera` (install via uv — both verified on PyPI). `fg-data-profiling` is unavailable on Py 3.9 → use `ydata-profiling` or skip profiling entirely.

**Local environment caveat for the planner:** the machine runs **Python 3.9.13**, below STACK.md's recommended 3.12. DuckDB 1.4.x, pandas 2.3.x, pyarrow 21.x, pandera 0.26.x all support 3.9, so Phase 1 is unaffected. Only the heavy profiler (`fg-data-profiling`/newer ydata-profiling lines) requires ≥3.10. If reproducibility on 3.12 is desired, `uv python pin 3.12` can provision it.

## Validation Architecture

> nyquist_validation is enabled (config: `workflow.nyquist_validation: true`). This section is the source for VALIDATION.md derivation.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (install via `uv add --dev pytest`) |
| Config file | none yet — Wave 0 creates `tests/conftest.py` (+ optional `pytest.ini`/`pyproject [tool.pytest]`) |
| Quick run command | `uv run pytest tests/test_rowcounts.py tests/test_nulls.py -x -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior (assertion) | Test Type | Automated Command | File Exists? |
|--------|----------------------|-----------|-------------------|-------------|
| DATA-01 | `bronze_availability` row count **== 4,614** | unit | `uv run pytest tests/test_rowcounts.py::test_availability_rowcount -x` | ❌ Wave 0 |
| DATA-01 | `bronze_utilization` row count **== 2,086** | unit | `uv run pytest tests/test_rowcounts.py::test_utilization_rowcount -x` | ❌ Wave 0 |
| DATA-01 | `bronze_ferry` row count **== 272,529** | unit | `uv run pytest tests/test_rowcounts.py::test_ferry_rowcount -x` | ❌ Wave 0 |
| DATA-01 | each table has its explicit column set / dtypes (esp. `UNIT_NO` VARCHAR, `AVAILABILITY_YTD` DOUBLE) | unit (Pandera) | `uv run pytest tests/test_schemas.py -x` | ❌ Wave 0 |
| DATA-03 | `AVAILABILITY_YTD` **null count == 209** | unit | `uv run pytest tests/test_nulls.py::test_null_count -x` | ❌ Wave 0 |
| DATA-03 | `AVAILABILITY_YTD` **non-null count == 4,405** | unit | `uv run pytest tests/test_nulls.py::test_nonnull_count -x` | ❌ Wave 0 |
| DATA-03 | **zero rows where an originally-null value became 0** — i.e. the count of rows that were blank in the CSV yet read as `0.0` is **0** (enforce by typing as DOUBLE and asserting `null_count + nonnull_count == total` with `nonnull == 4405`; the 209 stay NULL, never coerced) | unit | `uv run pytest tests/test_nulls.py::test_no_null_became_zero -x` | ❌ Wave 0 |
| DATA-04 | `AVAILABILITY_YTD` all non-null values within **[0.0, 1.0]** (availability 0–1 bounds) | unit (Pandera `Check.in_range(0,1)`) | `uv run pytest tests/test_schemas.py::test_availability_bounds -x` | ❌ Wave 0 |
| DATA-04 | `Utilization` value set **== {Underutilized, Not Underutilized}**; `Specialized units` **== {Yes, No}** | unit (Pandera `Check.isin`) | `uv run pytest tests/test_schemas.py::test_value_sets -x` | ❌ Wave 0 |
| DATA-02 | DQ-report observable outputs exist and carry the headline numbers: ferry **Sales median == 12**, **max == 7,229**; underutilized share **== 5.8%** (120/2,086); `OWNER_DIVISION` distinct **== 21**; `YEAR` range **1982–2026** | unit (assert on `profile.py` output dict) + artifact-exists check | `uv run pytest tests/test_profile.py -x` | ❌ Wave 0 |

**Null-preservation assertion detail (DATA-03, the load-bearing test):**
```python
total, non_null, null_ct = con.execute("""
  SELECT COUNT(*), COUNT(AVAILABILITY_YTD), COUNT(*) - COUNT(AVAILABILITY_YTD)
  FROM bronze_availability
""").fetchone()
assert total == 4614
assert non_null == 4405          # denominator for every availability rate
assert null_ct == 209            # genuine NULL, flagged DQ gap, NOT imputed
# "zero originally-null-became-0 == 0": because the column is typed DOUBLE and never
# COALESCE'd/filled, no blank can surface as 0.0. The guard is that non_null stays 4405
# (a fill would push it to 4614). Optionally assert there is no anomalous 0.0 spike.
```

### Availability 0–1 bounds assertion (DATA-04)
```python
# Pandera (preferred — declarative) OR direct SQL guard:
bad = con.execute("""
  SELECT COUNT(*) FROM bronze_availability
  WHERE AVAILABILITY_YTD IS NOT NULL AND (AVAILABILITY_YTD < 0 OR AVAILABILITY_YTD > 1)
""").fetchone()[0]
assert bad == 0   # verified this session: min 0.0, max 1.0
```

### DQ-report / profiling observable outputs (DATA-02)
The profiling step (`profile.py`) must emit a deterministic structure (dict → `dq_report.md`) containing, at minimum:
- per-table row counts (4,614 / 2,086 / 272,529)
- `AVAILABILITY_YTD`: null %, min, max, median
- ferry `Sales Count` median (12) and max (7,229); `Redemption Count` median (11) / max (7,216); skew note
- underutilization rate 5.8% with the **5.8% vs 14% discrepancy** framed as a stated insight (A2 citation)
- distinct division count (21), category-class count (19), YEAR range (1982–2026)
- the retired-dataset pull-date caveat (A1, cited)
These values are testable (`tests/test_profile.py`) and double as the DQ-report content.

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_rowcounts.py tests/test_nulls.py -x -q`
- **Per wave merge:** `uv run pytest -q`
- **Phase gate:** full suite green before `/gsd:verify-work` (this is the hard gate that unlocks Phase 2)

### Wave 0 Gaps
- [ ] `tests/conftest.py` — session fixture: connect DuckDB, run `ingest.py` into Bronze once
- [ ] `tests/test_rowcounts.py` — DATA-01 (3 parametrized count assertions)
- [ ] `tests/test_nulls.py` — DATA-03 (null==209, non-null==4405, no-null-became-0)
- [ ] `tests/test_schemas.py` — DATA-04 (Pandera: 0–1 bounds, value sets, dtypes)
- [ ] `tests/test_profile.py` — DATA-02 (profiling output numbers + DQ-report artifact exists)
- [ ] `src/fleet_analytics/schemas.py` — Pandera schemas
- [ ] Framework install: `uv add --dev pytest "pandera>=0.26"`

## Security Domain

No `security_enforcement` key set in config (defaults to enabled), but this phase reads local, public, Open-Government-Licence CSVs with **no auth, no network ingress, no user input, no secrets**. ASVS categories V2–V6 do not apply (no authentication, sessions, access control, or cryptography surface). The only relevant control is **input validation (V5)** — satisfied by the Pandera DQ contracts that reject malformed/out-of-range data. No threat patterns (injection, tampering) apply to a local read-only CSV→DuckDB ingest. No secrets are introduced.

## Sources

### Primary (HIGH confidence)
- **Direct DuckDB read of all three source CSVs (this session, 2026-06-02)** — every numeric DQ fact (row counts, 209/4,405 null split, 0–1 bounds, ferry median 12 / max 7,229, division/class counts, YEAR range, value sets).
- `pip index versions duckdb|pandera|ydata-profiling` and local imports — verified installable versions (DuckDB 1.4.4, pandas 2.3.3, pyarrow 21.0.0, pandera 0.26.1, ydata-profiling 4.17.0).
- `slopcheck install ...` 0.6.1 — all 9 packages [OK].
- `CLAUDE.md` (PROJECT/STACK/Constraints), `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` — locked decisions and success criteria.
- DuckDB CSV import docs — https://duckdb.org/docs/data/csv/overview ; `SUMMARIZE` — https://duckdb.org/docs/sql/statements/summarize `[CITED]`
- Pandera docs — https://pandera.readthedocs.io/ `[CITED]`

### Secondary (MEDIUM confidence)
- STACK.md guidance embedded in CLAUDE.md (used for stack rationale; version claims corrected against live registry).

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- DQ facts / assertion targets: **HIGH** — verified against the actual CSVs this session.
- Standard stack / versions: **HIGH** — verified against PyPI; STACK.md version drift corrected.
- Architecture / patterns: **HIGH** — standard DuckDB+Pandera+pytest patterns from official docs.
- Pitfalls: **HIGH** — derived from observed data shape (zero-padding, blanks, skew, filename).

**Research date:** 2026-06-02
**Valid until:** 2026-07-02 (stable; re-verify package versions if the lockfile is regenerated)
