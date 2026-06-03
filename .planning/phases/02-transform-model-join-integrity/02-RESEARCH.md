# Phase 2: Transform, Model & Join Integrity - Research

**Researched:** 2026-06-02
**Domain:** DuckDB SQL-first dimensional modeling (Bronze → Gold star schema), join-integrity testing, type-preserving Parquet/CSV export for Power BI
**Confidence:** HIGH (every SQL pattern below was executed against the real Phase 1 Bronze tables on the installed stack — DuckDB 1.5.3, pandas 3.0.3, pyarrow 24.0.0 — and reproduced the locked target numbers exactly)

## Summary

Phase 2 builds the Gold star schema on top of the three Phase 1 Bronze tables (`bronze_availability` 4,614 / `bronze_utilization` 2,086 / `bronze_ferry` 272,529) produced by `fleet_analytics.ingest.ingest_bronze(con)`. The work is overwhelmingly expressible as DuckDB SQL with a thin pandas boundary only if you prefer it for calendar generation (and even that is cleaner in pure DuckDB `generate_series` here — see below). All twelve locked decisions (D-01…D-12) are mechanically reproducible; the planner's job is to sequence them into `transform`/`model`/`export` modules with the join-integrity test as the hard gate.

The single most important discovery — verified live, not assumed — is the **canonical-key normalization strategy**. The utilization `UNIT_NO` column is 100% numeric (0 non-castable, 0 nulls, 0 whitespace). The availability `UNIT_NO` column has **44 genuinely alphanumeric values** (e.g. `296011A`, `383001B`, `CLAW10`) that are real fleet units and *cannot* become integers. A naïve `CAST(UNIT_NO AS BIGINT)` would null those 44 keys — which is harmless for the join (they're not light-duty, so they never match utilization anyway) but **must not drop them from `fact_vehicle`**, which D-01 requires to stay exactly 4,614 rows. The recommended pattern uses `TRY_CAST(UNIT_NO AS BIGINT)` as the *join key only*, while `fact_vehicle` is anchored on the full availability table via `LEFT JOIN`, so the 44 alphanumeric units survive with a NULL `unit_key_int` and NULL utilization attributes. This exact pattern was executed and reproduced **matched == 2,080, unmatched == 6, fact_vehicle == 4,614, no fan-out**.

**Primary recommendation:** Build the entire Gold layer in DuckDB SQL on the same `:memory:` connection pattern as `tests/conftest.py`, in a new `fleet_analytics/transform.py` (key normalization + derived fields) + `model.py` (the five Gold tables + join) + `export.py` (Parquet/CSV COPY). Use `TRY_CAST(UNIT_NO AS BIGINT)` as the canonical join key, `LEFT JOIN` anchored on availability for `fact_vehicle`, an anti-join for the 6 unmatched rows, `time_bucket` for 15-minute ferry slots, DuckDB `generate_series` for both `dim_date` and `dim_time`, and one `COPY … (FORMAT PARQUET)` + one `COPY … (FORMAT CSV, HEADER)` per Gold table. Gate the phase on a `test_join_integrity.py` that asserts the four join invariants against the reused `con` fixture.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**fact_vehicle grain & join**
- **D-01:** `fact_vehicle` is anchored on the **full fleet — all 4,614 availability rows** — with a **LEFT JOIN to utilization**. `Utilization` and `Specialized units` (and any using-division attribute) are NULL for the ~2,528 non-light-duty units. Rationale: availability-by-asset-class must span the whole fleet; the disposal-candidate cross-measure runs on the matched light-duty subset.
- **D-02:** The join is `bronze_availability LEFT JOIN bronze_utilization` on the normalized canonical-integer `UNIT_NO`. Matched (utilization present) == 2,080. A join-integrity test must assert: matched == 2,080, no NaN/NULL join key on the utilization side post-normalization, no fan-out (fact_vehicle stays exactly 4,614 rows — unique `fact_vehicle` key), and the utilization side reconciles as 2,080 matched + 6 unmatched == 2,086.
- **D-03:** The **6 unmatched** rows are surfaced via an **anti-join** (`bronze_utilization LEFT JOIN bronze_availability … WHERE availability IS NULL`), documented as a **DQ finding**, and guarded by a **test asserting unmatched count == 6**. These 6 rows fall outside `fact_vehicle` — that is expected.

**dim_division (conformed, role-playing)**
- **D-04:** Build **one conformed `dim_division`** with a surrogate key over the **distinct union of normalized division names** from both `OWNER_DIVISION` (availability, 21) and `REF_USING_DIV` (utilization, 20). Different roles (owns vs uses).
- **D-05:** `fact_vehicle` carries **two role-playing FKs**: `owner_division_key` (always populated, from `OWNER_DIVISION`) and `using_division_key` (light-duty only, **nullable**, from `REF_USING_DIV`).
- **D-06:** Name reconciliation = **normalize (trim, collapse internal whitespace, uppercase) + distinct union**. Do **not** force-map spellings. Surface any owner/using names that do not reconcile as a **documented DQ finding**. `OWNER_DIVISION` is truncated in source (e.g. `"ENVIRONMENT, CLIMATE & FORESTR"`) — preserve as-is, document the truncation.

**Vehicle derived field — fleet_age**
- **D-07:** `fleet_age = REFERENCE_YEAR − model YEAR` (manufacture age). Use model `YEAR` (no nulls), not `IN_SERV_DT`.
- **D-08:** `REFERENCE_YEAR` is a **config constant in `config.py`**, set to **2023**. Document the chosen value + rationale (May 2023 FSD report / audit 2022-2023 benchmark context).

**Ferry derived fields**
- **D-09:** `season` = **meteorological 4-season by month**: Dec–Feb Winter, Mar–May Spring, Jun–Aug Summer, Sep–Nov Fall.
- **D-10:** `daypart` = **4 bands** on hour-of-day: Morning 06:00–11:00, Midday 11:00–15:00, Afternoon/Evening 15:00–20:00, Night 20:00–06:00.
- **D-11:** `sales_redemption_gap` = **`Sales Count − Redemption Count`** per 15-min row. Signed — do **not** use absolute value.
- **D-12:** `day_of_week` and `is_weekend` (Sat/Sun) are mechanical derivations from the parsed timestamp.

### Claude's Discretion
- Surrogate-key generation strategy for `dim_division`, `dim_date`, `dim_time` (`ROW_NUMBER()`/sequence vs natural date keys) — planner's call, star-schema-consistent.
- DuckDB persistence model for the Gold build (in-memory build → COPY to Parquet vs a `.duckdb` file) — in-memory is consistent with the Phase 1 conftest pattern.
- Exact `dim_date` / `dim_time` attribute columns beyond locked constraints (gapless 2015→2026; 96 rows).
- Whether derived bucket boundaries live as SQL `CASE` expressions or small lookup tables.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (KPI computation, DAX measures, Power BI report spec are Phases 3–4; narrative deliverables are Phase 5.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MODEL-01 | `UNIT_NO` normalized to canonical integer on both datasets; ferry timestamps parsed tz-naive and rounded to 15-min slots; derived fields (`fleet_age`, `season`, `daypart`, `day_of_week`, `is_weekend`, `sales_redemption_gap`) produced | Normalization SQL (§Code Examples 1) verified `TRY_CAST` handles the 44 alnum units; `time_bucket` 15-min rounding verified 0 NaT / 272,529 rows preserved (§Code Examples 3); derived-field CASE/scalar SQL verified (§Code Examples 4) |
| MODEL-02 | Gold tables built — `dim_division`, `fact_vehicle` (degenerate enriched dim), `fact_ferry`, gapless `dim_date` (2015→2026), 96-row `dim_time` | `dim_division` normalized union verified → 21 rows (§Code Examples 5); `generate_series` `dim_date` verified gapless 4,383 days; `dim_time` verified exactly 96 rows (§Code Examples 6) |
| MODEL-03 | Availability ⋈ utilization on normalized `UNIT_NO`; join-integrity tests asserting matched==2,080, unmatched==6, unique `fact_vehicle` key, no fan-out; 6 unmatched documented as DQ finding | LEFT JOIN + anti-join SQL executed live → matched 2,080 / unmatched 6 / fact 4,614 / 0 dup keys (§Code Examples 2); pytest assertion shapes provided (§Validation Architecture) |
| MODEL-04 | All five Gold tables exported as type-preserving Parquet (plus readable CSV) ready for Power BI | `COPY … FORMAT PARQUET` verified preserving DOUBLE+209 NULLs+DATE; CSV reread preserved 209 nulls (§Code Examples 7) |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `UNIT_NO` key normalization | DuckDB SQL (transform) | — | Set-based `TRY_CAST`/`TRIM`; testable as a column expression. CLAUDE.md DuckDB-vs-pandas table assigns normalization+join to DuckDB SQL. |
| availability⋈utilization join | DuckDB SQL (model) | — | The flagship value-added step; `LEFT JOIN` + anti-join make match/miss counts explicit, testable queries. |
| Derived vehicle/ferry fields | DuckDB SQL (transform) | — | `date_part`/`CASE` set-based derivations are concise and self-documenting; CLAUDE.md assigns these to SQL. |
| `dim_date` / `dim_time` generation | DuckDB SQL `generate_series` | pandas `pd.date_range` (alt) | Both produce 4,383 days / 96 slots; DuckDB keeps everything on one connection with no register step (see Discretion recommendation). |
| `dim_division` conformed dim | DuckDB SQL (model) | — | Distinct-union + `ROW_NUMBER()` surrogate is one statement. |
| Parquet/CSV export | DuckDB SQL `COPY` (export) | — | One statement per table; preserves types into Parquet natively. CLAUDE.md mandates `COPY … FORMAT PARQUET`. |
| Join-integrity / dim / derived tests | pytest + DuckDB (reuse `con` fixture) | Pandera (optional Gold contracts) | Phase 1 established the `con` session fixture + count-assertion pattern; Phase 2 extends it. |

## Standard Stack

### Core
| Library | Version (installed, verified) | Purpose | Why Standard |
|---------|-------------------------------|---------|--------------|
| DuckDB (Python client) | **1.5.3** | All Bronze→Gold SQL transforms, join, aggregation, `generate_series` dims, Parquet/CSV export | In-process OLAP; the entire phase is SQL on one connection. [VERIFIED: `uv run python -c "import duckdb; print(duckdb.__version__)"` → 1.5.3] |
| pandas | **3.0.3** | Optional boundary for `dim_date`/`dim_time` if preferred; test assertions / `.df()` reads | Installed and DuckDB-interoperable. [VERIFIED: import → 3.0.3] |
| pyarrow | **24.0.0** | Parquet read/write engine behind DuckDB `COPY` and pandas `to_parquet` | De-facto Parquet engine. [VERIFIED: import → 24.0.0] |
| pytest | **>=9.0.3** (dev group) | Test runner for join-integrity + derived + dim tests | Phase 1 suite (24 tests) uses it; reuse the `con` fixture. [VERIFIED: pyproject dev group] |
| Pandera | **>=0.26** (dev group) | OPTIONAL declarative Gold-tier contracts (e.g. `fleet_age` integer, `season ∈ {…}`) | Already a dev dep from Phase 1 `schemas.py`. [VERIFIED: pyproject dev group] |

> **IMPORTANT — version drift correction.** The task brief and `.planning/STATE.md` reference `duckdb>=1.4,<1.5` (1.5.x "not on PyPI"). That is **stale**. The installed environment is **DuckDB 1.5.3** and `pyproject.toml` already pins `duckdb>=1.5,<2`, `pandas>=2.2` (resolved to 3.0.3), `pyarrow>=16` (resolved to 24.0.0). PROJECT.md's own footer confirms "24 tests green on DuckDB 1.5.3". Plan against **1.5.3 / pandas 3.0.3 / pyarrow 24.0.0** — all SQL in this document was executed on that exact stack. `[VERIFIED: uv run import checks 2026-06-02]`

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas `date_range` | bundled (3.0.3) | Alternative `dim_date` spine generation | Only if the planner prefers a pandas frame registered via `con.register("dim_date_df", df)` then `FROM dim_date_df`. Not recommended here (DuckDB `generate_series` is cleaner — see Discretion). |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| DuckDB `generate_series` for dims | pandas `pd.date_range` + `con.register` | pandas adds a register round-trip and a second engine for zero benefit at this scale; both yield 4,383 days. Stay in SQL. |
| `TRY_CAST(UNIT_NO AS BIGINT)` join key | `regexp_replace`-then-strip-zeros string key | A string-stripped key would *match* the 44 alnum units as themselves, but since they never appear in utilization it changes nothing — and an integer key is simpler to assert "no NULL on the matched side". Integer key recommended. |
| `time_bucket` for 15-min slots | `date_trunc` arithmetic | Ferry timestamps are *already* on 15-min boundaries (verified: 0 off-grid rows), so both are no-ops here; `time_bucket(INTERVAL '15 minutes', ts)` is the explicit, defensible choice and is robust if a future re-supply is off-grid. |
| In-memory build + COPY | `.duckdb` file | A persisted file adds stale-state risk and a cleanup burden; in-memory matches the conftest pattern. Use in-memory. |

**Installation:** No new dependencies required. The entire phase runs on the existing `duckdb`, `pandas`, `pyarrow`, `pytest`, `pandera` already in `pyproject.toml`. Run everything via `uv run` (system Python is 3.9.13; project is pinned to 3.12 — see MEMORY.md).

**Version verification performed:**
```bash
uv run python -c "import duckdb, pandas, pyarrow; print(duckdb.__version__, pandas.__version__, pyarrow.__version__)"
# → 1.5.3 3.0.3 24.0.0   [VERIFIED 2026-06-02]
```

## Package Legitimacy Audit

> No new external packages are installed in this phase — all four libraries (`duckdb`, `pandas`, `pyarrow`, `pytest`/`pandera`) were vetted and installed in Phase 1 and are already pinned in `pyproject.toml`. Slopcheck/registry verification is **not applicable** for Phase 2 because the package set is unchanged from the Phase-1 baseline.

| Package | Registry | Status | Disposition |
|---------|----------|--------|-------------|
| duckdb | PyPI | Pre-installed Phase 1, pinned `>=1.5,<2` | Approved (no change) |
| pandas | PyPI | Pre-installed Phase 1, pinned `>=2.2` | Approved (no change) |
| pyarrow | PyPI | Pre-installed Phase 1, pinned `>=16` | Approved (no change) |
| pytest / pandera | PyPI | Pre-installed Phase 1 dev group | Approved (no change) |

**Packages removed due to slopcheck [SLOP] verdict:** none (no installs this phase)
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                      ┌─────────────────────────────────────────────┐
                      │  ingest_bronze(con)  [Phase 1, reused as-is]  │
                      └──────────────────────┬──────────────────────┘
                                             │  3 Bronze tables on a DuckDB con
          ┌──────────────────────────────────┼───────────────────────────────────┐
          ▼                                  ▼                                   ▼
  bronze_availability (4614)        bronze_utilization (2086)             bronze_ferry (272529)
          │                                  │                                   │
          │  transform.py: add unit_key_int = TRY_CAST(UNIT_NO AS BIGINT)        │  transform.py:
          │  + fleet_age = REFERENCE_YEAR - YEAR                                  │  ts_15 = time_bucket(15min, Timestamp)
          │  + normalized owner/using division names                             │  + season/daypart/day_of_week/
          ▼                                  ▼                                   │    is_weekend/sales_redemption_gap
   ┌──────────────┐  LEFT JOIN on   ┌──────────────┐                             ▼
   │ av (keyed)   │◄────────────────│ ut (keyed)   │                       ┌────────────┐
   └──────┬───────┘  unit_key_int   └──────┬───────┘                       │ fact_ferry │
          │  anchored on availability      │  anti-join (WHERE av IS NULL) │ (272529)   │
          ▼                                ▼                               └─────┬──────┘
   ┌──────────────────────────┐    ┌────────────────────┐                       │
   │ fact_vehicle (4614)      │    │ 6 unmatched rows    │                       │
   │  +Utilization (2080 nn)  │    │  → DQ finding        │                       │
   │  +owner_division_key     │    └────────────────────┘                       │
   │  +using_division_key(nbl)│                                                   │
   └──────────┬───────────────┘                                                   │
              │  FK → dim_division (21, conformed, ROW_NUMBER surrogate)          │
              ▼                                                                    ▼
   ┌────────────────────────────── model.py builds 5 Gold tables ───────────────────────────┐
   │  dim_division(21) · fact_vehicle(4614) · fact_ferry(272529) · dim_date(4383) · dim_time(96) │
   └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                ▼  export.py: COPY per table
                              data/gold/*.parquet  (+ *.csv readable secondary)
                                                ▼
                                  Power BI import [Phase 4, manual]
```

### Recommended Project Structure
```
src/fleet_analytics/
├── config.py        # EXTEND: add REFERENCE_YEAR = 2023 (D-08); GOLD_DIR; GOLD_TABLES list
├── ingest.py        # UNCHANGED (Phase 1) — ingest_bronze(con)
├── transform.py     # NEW: keyed/derived Bronze→staging views (unit_key_int, fleet_age, ferry derived fields, normalized division names)
├── model.py         # NEW: build the 5 Gold tables on con (dim_division, fact_vehicle, fact_ferry, dim_date, dim_time) + the LEFT JOIN/anti-join
├── export.py        # NEW: COPY each Gold table to data/gold/*.parquet + *.csv
├── schemas.py       # OPTIONAL EXTEND: Gold-tier Pandera contracts
└── profile.py       # UNCHANGED

tests/
├── conftest.py      # EXTEND: add a session/module fixture `gold` that runs transform+model on the existing `con`
├── test_join_integrity.py   # NEW — the hard gate (matched/unmatched/fan-out/unique key)
├── test_derived_fields.py   # NEW — parametrized fleet_age/season/daypart/dow/is_weekend/gap cases
├── test_dimensions.py       # NEW — dim_date gapless, dim_time == 96, dim_division conformed (21)
└── test_export.py           # NEW — Parquet/CSV roundtrip type+null preservation
```

### Pattern 1: Keyed staging views, then Gold tables (DuckDB SQL-first)
**What:** `transform.py` adds the canonical key and derived columns as `CREATE OR REPLACE VIEW` (or `TABLE`) over Bronze; `model.py` consumes those to build Gold. Mirrors `ingest._create_bronze`'s `CREATE OR REPLACE TABLE … AS SELECT` style.
**When to use:** Always here — keeps each transform a single testable SQL statement and reuses the one `con`.
**Example:**
```python
# Source: pattern mirrors src/fleet_analytics/ingest.py::_create_bronze (CREATE OR REPLACE TABLE AS SELECT)
def build_keyed_availability(con):
    con.execute("""
        CREATE OR REPLACE TABLE stg_availability AS
        SELECT *,
               TRY_CAST(UNIT_NO AS BIGINT) AS unit_key_int,
               (? - YEAR) AS fleet_age
        FROM bronze_availability
    """, [config.REFERENCE_YEAR])
```

### Pattern 2: Anchor fact on the larger table via LEFT JOIN (no fan-out by construction)
**What:** `fact_vehicle` = availability `LEFT JOIN` utilization on `unit_key_int`. Because `UNIT_NO` is unique across all 4,614 availability rows (verified: `COUNT(*) == COUNT(DISTINCT UNIT_NO) == 4614`) and utilization has zero duplicate keys, the LEFT JOIN cannot fan out.
**When to use:** The flagship join (D-01/D-02).

### Pattern 3: Reuse the `con` fixture; build Gold once per test session
**What:** Phase 1's `tests/conftest.py` yields a session-scoped `:memory:` `con` with Bronze ingested. Add a fixture that builds Gold on that same connection so all Phase-2 tests query real Gold tables without re-ingesting.
**Example:**
```python
# tests/conftest.py — extend
@pytest.fixture(scope="session")
def gold(con):
    from fleet_analytics import transform, model
    transform.build_all(con)
    model.build_all(con)
    return con
```

### Anti-Patterns to Avoid
- **`CAST(UNIT_NO AS BIGINT)` (non-TRY) on availability:** throws on the 44 alphanumeric units (`296011A`, `CLAW10`, …). Always `TRY_CAST` so those become a NULL *join key* while the row survives in `fact_vehicle`.
- **`INNER JOIN` for fact_vehicle:** drops the ~2,528 non-light-duty units and breaks the full-fleet availability-by-class KPI (violates D-01).
- **COALESCE / fill on `AVAILABILITY_YTD`:** the 209 NULLs must survive into Gold and into Parquet (verified preserved). Phase 1 `test_nulls.py` is the regression guard — do not break it.
- **Forcing division spelling maps:** D-06 forbids it. Normalize (trim/collapse-ws/upper) + distinct union only; truncated names (`ENVIRONMENT, CLIMATE & FORESTR`) stay verbatim.
- **A `.duckdb` file for the Gold build:** introduces stale state across test runs; use `:memory:` + COPY-to-disk for the Parquet outputs only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 15-min timestamp rounding | Manual minute arithmetic / Python loops | DuckDB `time_bucket(INTERVAL '15 minutes', "Timestamp")` | One scalar; 0 NaT; 272,529 rows preserved (verified). |
| Gapless calendar spine | Python date loop appending rows | DuckDB `generate_series(DATE '2015-01-01', DATE '2026-12-31', INTERVAL '1 day')` | Gapless by construction; verified 4,383 rows. |
| 96 time-of-day slots | Hard-coded 96-row literal table | `generate_series(TIMESTAMP '…00:00', '…23:45', INTERVAL '15 minutes')` cast to TIME | Verified exactly 96 rows; self-documenting. |
| Surrogate keys | UUIDs / hash columns | `ROW_NUMBER() OVER (ORDER BY division_name)` | Star-schema-idiomatic, stable, integer-typed, sorts cleanly. |
| Type-preserving export | pandas `to_csv` then re-typing in Power Query | DuckDB `COPY (…) TO 'x.parquet' (FORMAT PARQUET)` | Dates stay DATE, AVAILABILITY_YTD stays DOUBLE+NULL, booleans stay boolean (verified roundtrip). |
| Division name normalization | Per-row Python `.strip().upper()` | `upper(trim(regexp_replace(col,'\s+',' ','g')))` in SQL | Set-based, one statement; feeds the distinct-union dim directly. |

**Key insight:** Every Phase-2 transformation is a set operation DuckDB already does in one SQL statement. The value the planner adds is *sequencing + assertion*, not algorithm-building.

## Runtime State Inventory

> This phase is a **greenfield Gold build** over existing Bronze tables — it creates new tables and new Parquet/CSV files; it renames nothing and migrates no stored runtime state. The categories below are answered explicitly per protocol.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — `:memory:` DuckDB rebuilt from CSV each run via `ingest_bronze`; no persistent datastore holds keys to migrate. | None |
| Live service config | None — no external service (no n8n/Datadog/etc.); pipeline is single-machine. | None |
| OS-registered state | None — no scheduled tasks/daemons; pipeline runs via `uv run`. | None |
| Secrets/env vars | Only `FLEET_DATA_DIR` (optional CSV-dir override, read in `config.py`). New `REFERENCE_YEAR` is a plain module constant, not a secret/env var. | None — add `REFERENCE_YEAR = 2023` as a `config.py` constant (D-08). |
| Build artifacts | New `data/gold/*.parquet` + `*.csv` are *created* this phase (not stale). Ensure `data/gold/` exists / is gitignored-or-shipped per SHIP-01 (Phase 6 concern). | Create `data/gold/` on export; no stale artifact to clean. |

**The canonical question — "after every file is updated, what runtime systems still have the old string cached/stored/registered?"** — has no applicable answer here: nothing is being renamed. New constant (`REFERENCE_YEAR`) and new outputs only.

## Common Pitfalls

### Pitfall 1: Naïve integer cast silently drops the 44 alphanumeric availability units
**What goes wrong:** `CAST(UNIT_NO AS BIGINT)` throws; `TRY_CAST` returns NULL for `296011A`/`CLAW10`/etc. If you then `INNER JOIN` or filter `WHERE unit_key_int IS NOT NULL` before building `fact_vehicle`, you lose 44 real fleet vehicles and `fact_vehicle` drops below 4,614 (breaks D-01 and MODEL-02).
**Why it happens:** Assuming all `UNIT_NO` values are numeric (utilization is; availability is not).
**How to avoid:** Use `TRY_CAST` as the *join key only*; anchor `fact_vehicle` on the full availability table with `LEFT JOIN`. Assert `COUNT(*) == 4614` on `fact_vehicle`.
**Warning signs:** `fact_vehicle` rowcount == 4,570 (4,614 − 44) instead of 4,614.

### Pitfall 2: The 6 unmatched rows are invisible to fact_vehicle by design
**What goes wrong:** Looking for the 6 unmatched utilization rows inside `fact_vehicle` and finding zero, then concluding the join is wrong.
**Why it happens:** `fact_vehicle` is availability-anchored; the 6 unmatched are *utilization* rows with no availability match, so they cannot appear in an availability-anchored fact.
**How to avoid:** Surface them only via the anti-join (`bronze_utilization LEFT JOIN … WHERE availability IS NULL`); assert count == 6; write them to the DQ finding (D-03).
**Warning signs:** Test trying to find 6 NULL-availability rows *in* fact_vehicle.

### Pitfall 3: Breaking the Phase-1 null-preservation guard
**What goes wrong:** A `COALESCE(AVAILABILITY_YTD, 0)` or a pandas `fillna` slips into the Gold build; `test_nulls.py` (209-null guard) and the Parquet null-count test go red.
**Why it happens:** Reflexive null-filling during modeling.
**How to avoid:** Never touch `AVAILABILITY_YTD` nullability. Verified: Parquet export preserves all 209 NULLs as genuine NULL.
**Warning signs:** non-null count drifts from 4,405 toward 4,614.

### Pitfall 4: `date_part('month'…)` literal vs identifier
**What goes wrong:** `date_part("month", ts)` (double quotes) is a Binder Error — DuckDB reads `"month"` as a column reference. (Confirmed live.)
**How to avoid:** Use single-quoted part name `date_part('month', ts)` **or** the dedicated scalar functions `month(ts)`, `hour(ts)`, `isodow(ts)`, `dayname(ts)` (all verified working). The scalar functions read more clearly in the `CASE` expressions.

### Pitfall 5: `fleet_age` can be negative
**What goes wrong:** Model `YEAR` ranges 1982→2026; `2023 − 2026 = −3`. Verified `fleet_age` range is **−3 … 41**. A naïve "age must be ≥ 0" Pandera/test check would falsely fail.
**How to avoid:** Document that negative ages reflect future-model-year units (2024–2026); do **not** clamp. If you assert a bound, use `fleet_age BETWEEN -5 AND 60` or no lower bound.

### Pitfall 6: Reserved words as column aliases in test SQL
**What goes wrong:** Aliasing a column `both` or `nulls` is a Parser Error (confirmed live).
**How to avoid:** Use `in_both`, `null_ct`, etc. (Phase 1 `test_nulls.py` already uses `null_ct`.)

## Code Examples

> Every snippet below was executed against the real Bronze tables on DuckDB 1.5.3 and produced the stated result. `[VERIFIED: live execution 2026-06-02]`

### Example 1 — Canonical key normalization (handles the 44 alphanumeric units)
```python
# Source: live-verified against bronze_availability / bronze_utilization
# avail non-numeric UNIT_NO == 44 (e.g. '296011A','CLAW10'); util non-numeric == 0; both 0 nulls/0 whitespace
con.execute("""
    CREATE OR REPLACE TABLE stg_availability AS
    SELECT *, TRY_CAST(UNIT_NO AS BIGINT) AS unit_key_int
    FROM bronze_availability
""")
con.execute("""
    CREATE OR REPLACE TABLE stg_utilization AS
    SELECT *, TRY_CAST(UNIT_NO AS BIGINT) AS unit_key_int
    FROM bronze_utilization
""")
# Assert: every utilization key is non-NULL post-normalization (D-02 "no NaN join key")
# SELECT COUNT(*) FILTER (WHERE unit_key_int IS NULL) FROM stg_utilization  -> 0  [VERIFIED]
```

### Example 2 — fact_vehicle LEFT JOIN + anti-join (matched 2,080 / unmatched 6 / fact 4,614)
```sql
-- fact_vehicle: availability-anchored LEFT JOIN  [VERIFIED: 4614 rows, 2080 utilization-non-null, 0 dup keys]
CREATE OR REPLACE TABLE fact_vehicle AS
SELECT a.*,
       u.Utilization,
       u."Specialized units" AS specialized_units,
       u.REF_USING_DIV
FROM stg_availability a
LEFT JOIN stg_utilization u
  ON a.unit_key_int = u.unit_key_int;

-- matched count  [VERIFIED == 2080]
SELECT COUNT(*) FROM fact_vehicle WHERE Utilization IS NOT NULL;

-- anti-join: the 6 unmatched utilization rows (DQ finding, D-03)  [VERIFIED == 6]
CREATE OR REPLACE TABLE dq_unmatched_utilization AS
SELECT u.*
FROM stg_utilization u
LEFT JOIN stg_availability a ON u.unit_key_int = a.unit_key_int
WHERE a.unit_key_int IS NULL;
-- reconciliation: 2080 matched + 6 unmatched == 2086 (full utilization)  [VERIFIED]
```
Verified invariants from live run: `fact rowcount: 4614`, `fact matched: 2080`, `unmatched util: 6`, `util dup keys: 0`, `avail dup keys: 0`.

### Example 3 — Ferry timestamp 15-min slot (no NaT, 272,529 preserved)
```sql
-- [VERIFIED: ferry15 rowcount 272529, ts_15 nulls 0, off-grid count 0]
CREATE OR REPLACE TABLE stg_ferry AS
SELECT *,
       time_bucket(INTERVAL '15 minutes', "Timestamp") AS ts_15
FROM bronze_ferry;
```

### Example 4 — Ferry derived fields (D-09…D-12), all scalar-verified
```sql
-- [VERIFIED sample: ('Summer','Night','Monday',false,-1) etc. — gap is signed]
SELECT
  CASE WHEN month("Timestamp") IN (12,1,2) THEN 'Winter'
       WHEN month("Timestamp") IN (3,4,5)  THEN 'Spring'
       WHEN month("Timestamp") IN (6,7,8)  THEN 'Summer'
       ELSE 'Fall' END                                   AS season,       -- D-09
  CASE WHEN hour("Timestamp") >= 6  AND hour("Timestamp") < 11 THEN 'Morning'
       WHEN hour("Timestamp") >= 11 AND hour("Timestamp") < 15 THEN 'Midday'
       WHEN hour("Timestamp") >= 15 AND hour("Timestamp") < 20 THEN 'Afternoon/Evening'
       ELSE 'Night' END                                  AS daypart,      -- D-10
  dayname("Timestamp")                                   AS day_of_week,  -- D-12
  (isodow("Timestamp") >= 6)                             AS is_weekend,   -- D-12 (Sat=6,Sun=7)
  "Sales Count" - "Redemption Count"                     AS sales_redemption_gap  -- D-11 (signed)
FROM bronze_ferry;
```

### Example 5 — Conformed dim_division (normalize + distinct union → 21 rows)
```sql
-- [VERIFIED: 21 rows; owner_norm 21, using_norm 20, intersection 20, union 21
--  => all 20 using-divisions reconcile inside the 21 owner-divisions; ZERO unreconciled names]
CREATE OR REPLACE TABLE dim_division AS
WITH names AS (
  SELECT DISTINCT upper(trim(regexp_replace(OWNER_DIVISION, '\s+', ' ', 'g'))) AS division_name
  FROM bronze_availability WHERE OWNER_DIVISION IS NOT NULL
  UNION
  SELECT DISTINCT upper(trim(regexp_replace(REF_USING_DIV, '\s+', ' ', 'g')))
  FROM bronze_utilization WHERE REF_USING_DIV IS NOT NULL
)
SELECT ROW_NUMBER() OVER (ORDER BY division_name) AS division_key, division_name
FROM names;

-- fact_vehicle role-playing FKs (D-05): join the normalized name back to dim_division
-- owner_division_key (always populated); using_division_key (NULL for non-light-duty)
```
> **DQ note for D-06:** the normalized union is exactly 21 (= owner count) because every using-division name is a subset of the owner names after normalization — so there are **no unreconciled names** to report (a clean DQ result). Still document the verbatim truncations (e.g. `ENVIRONMENT, CLIMATE & FORESTR`) in the data dictionary.

### Example 6 — dim_date (gapless 2015→2026, 4,383 rows) and dim_time (96 rows)
```sql
-- dim_date  [VERIFIED: 4383 rows, min 2015-01-01, max 2026-12-31; matches pandas date_range len]
CREATE OR REPLACE TABLE dim_date AS
SELECT
  CAST(d AS DATE)                       AS date_key,     -- natural date surrogate
  year(d)                               AS year,
  month(d)                              AS month,
  monthname(d)                          AS month_name,
  day(d)                                AS day,
  dayname(d)                            AS day_of_week,
  (isodow(d) >= 6)                      AS is_weekend,
  quarter(d)                            AS quarter
FROM generate_series(DATE '2015-01-01', DATE '2026-12-31', INTERVAL '1 day') AS t(d);

-- dim_time  [VERIFIED: exactly 96 rows]
CREATE OR REPLACE TABLE dim_time AS
SELECT
  ROW_NUMBER() OVER (ORDER BY CAST(g AS TIME)) AS time_key,
  CAST(g AS TIME)                              AS time_of_day,
  hour(g)                                      AS hour,
  minute(g)                                    AS minute
FROM generate_series(TIMESTAMP '2000-01-01 00:00', TIMESTAMP '2000-01-01 23:45', INTERVAL '15 minutes') AS s(g);
```
> **Surrogate-key recommendation (Discretion):** use the **natural `date_key` (DATE)** for `dim_date` (idiomatic; enables Power BI "Mark as Date Table" in Phase 4) and an **integer `ROW_NUMBER()` surrogate** for `dim_division` and `dim_time`. This is the standard star-schema mix.

### Example 7 — Type-preserving Parquet + readable CSV export
```sql
-- Parquet (primary)  [VERIFIED roundtrip: AVAILABILITY_YTD -> DOUBLE with 209 NULLs; IN_SERV_DT -> DATE]
COPY (SELECT * FROM fact_vehicle) TO 'data/gold/fact_vehicle.parquet' (FORMAT PARQUET);
-- CSV (readable secondary)  [VERIFIED: reread null count == 209 — blanks stay NULL, not 0]
COPY (SELECT * FROM fact_vehicle) TO 'data/gold/fact_vehicle.csv' (FORMAT CSV, HEADER);
```
```python
# export.py loop over the five Gold tables
GOLD_TABLES = ["dim_division", "fact_vehicle", "fact_ferry", "dim_date", "dim_time"]
for t in GOLD_TABLES:
    p = (config.GOLD_DIR / t).as_posix()
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.parquet' (FORMAT PARQUET)")
    con.execute(f"COPY (SELECT * FROM {t}) TO '{p}.csv' (FORMAT CSV, HEADER)")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `duckdb>=1.4,<1.5` "1.5 not on PyPI" (task brief / STATE.md) | **DuckDB 1.5.3 installed; pyproject pins `>=1.5,<2`** | Already current in repo (PROJECT.md footer: "24 tests green on DuckDB 1.5.3") | Plan against 1.5.3 — the brief's pin note is stale. |
| pandas `date_range` + register for spines | DuckDB `generate_series` directly | DuckDB 0.8+ `generate_series` on dates | Keeps dims on one connection, no pandas round-trip. |
| `date_trunc` minute math for buckets | `time_bucket(INTERVAL …, ts)` | DuckDB ≥0.9 | Explicit, off-grid-robust 15-min slotting. |

**Deprecated/outdated:**
- The `duckdb>=1.4,<1.5` constraint and the "1.5.x not on PyPI" note in `.planning/STATE.md` — superseded; installed env is 1.5.3 and pyproject already reflects `>=1.5,<2`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `data/gold/` is the intended output dir (REQUIREMENTS SHIP-01 says `data/gold/` with five Parquet files) | Export / structure | Low — explicitly stated in REQUIREMENTS.md SHIP-01; planner should add `GOLD_DIR` to `config.py`. |
| A2 | The natural-date `date_key` for `dim_date` + integer `ROW_NUMBER()` surrogates for `dim_division`/`dim_time` is the desired surrogate strategy (Discretion item) | Code Examples 5–6 | Low — both are star-schema-standard; either is acceptable per D-discretion. Planner confirms. |
| A3 | `dim_time` grain is the 96 quarter-hour slots of a day (time-of-day), keyed independently of `dim_date` | Code Examples 6 | Low — "96-row dim_time" is locked; 96 = 24×4 quarter-hours is the only reading that yields 96. |
| A4 | Extra `dim_date`/`dim_time` attribute columns (year/month/quarter/hour/minute/etc.) are welcome beyond the locked gapless/96 constraints (Discretion grants this) | Code Examples 6 | Low — Discretion explicitly leaves attribute columns to the planner. |

**Note:** No `[ASSUMED]` claims affect the locked numeric targets — every join/derived/dim count in this research was *verified by live execution*, not assumed.

## Open Questions

1. **Should the 44 alphanumeric availability `UNIT_NO` values get a DQ note too?**
   - What we know: 44 units (`296011A`, `CLAW10`, …) are non-integer; they correctly survive in `fact_vehicle` with NULL `unit_key_int` and never match utilization.
   - What's unclear: whether the data dictionary should call them out alongside the 6-unmatched finding.
   - Recommendation: add a one-line DQ note ("44 availability units carry alphanumeric IDs and are excluded from the integer join key by design") — cheap, defensible, strengthens the BA narrative. Planner's call.

2. **`fact_ferry` grain — keep all 272,529 rows or pre-aggregate?**
   - What we know: success criteria + ferry KPIs (heatmap, YoY, seasonality) all locked at 15-min grain; row count == 272,529 is a stated success criterion.
   - Recommendation: keep `fact_ferry` at full 15-min grain (272,529 rows) carrying `ts_15`, FKs to `dim_date`/`dim_time`, and the derived fields; aggregation is a Phase-3 KPI concern.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (via uv) | All transforms/tests | ✓ | 3.12 (project-pinned; system 3.9.13 — use `uv run`) | none needed |
| DuckDB | All SQL | ✓ | 1.5.3 | none needed |
| pandas | Optional dim spines / test reads | ✓ | 3.0.3 | DuckDB `generate_series` (preferred anyway) |
| pyarrow | Parquet COPY engine | ✓ | 24.0.0 | none needed |
| pytest | Test suite | ✓ | >=9.0.3 (dev) | none needed |
| pandera | Optional Gold contracts | ✓ | >=0.26 (dev) | plain pytest count asserts |
| Source CSVs | Bronze ingest (reused) | ✓ | `.planning/data/` (per `config.DATA_DIR`) | `FLEET_DATA_DIR` override |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none material — pandas is present but DuckDB `generate_series` is the recommended path regardless.

> Reminder (MEMORY.md): system Python is 3.9.13; run **everything** via `uv run` so the 3.12 project env is used.

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` → this section is included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=9.0.3 (+ optional Pandera >=0.26) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["src"]`) |
| Quick run command | `uv run pytest -q tests/test_join_integrity.py` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODEL-03 | matched == 2,080 | unit | `uv run pytest tests/test_join_integrity.py::test_matched_2080 -x` | ❌ Wave 0 |
| MODEL-03 | unmatched (anti-join) == 6 | unit | `… ::test_unmatched_6 -x` | ❌ Wave 0 |
| MODEL-03 | fact_vehicle == 4,614, no fan-out | unit | `… ::test_fact_rowcount_4614 -x` | ❌ Wave 0 |
| MODEL-03 | unique fact_vehicle key (UNIT_NO distinct == 4,614) | unit | `… ::test_fact_unique_key -x` | ❌ Wave 0 |
| MODEL-03 | utilization join key has no NULL post-normalization | unit | `… ::test_util_key_not_null -x` | ❌ Wave 0 |
| MODEL-01 | ferry 15-min slot: 0 NaT, 272,529 rows | unit | `tests/test_derived_fields.py::test_ferry_ts15 -x` | ❌ Wave 0 |
| MODEL-01 | fleet_age = 2023 − YEAR (parametrized cases) | unit | `… ::test_fleet_age[case] -x` | ❌ Wave 0 |
| MODEL-01 | season/daypart/day_of_week/is_weekend boundary cases | unit | `… ::test_season_daypart[case] -x` | ❌ Wave 0 |
| MODEL-01 | sales_redemption_gap signed (Sales − Redemption) | unit | `… ::test_gap_signed -x` | ❌ Wave 0 |
| MODEL-02 | dim_date gapless (count == 4,383, max−min+1 == count) | unit | `tests/test_dimensions.py::test_dim_date_gapless -x` | ❌ Wave 0 |
| MODEL-02 | dim_time == 96 rows | unit | `… ::test_dim_time_96 -x` | ❌ Wave 0 |
| MODEL-02 | dim_division conformed == 21, surrogate keys unique | unit | `… ::test_dim_division_conformed -x` | ❌ Wave 0 |
| MODEL-04 | Parquet roundtrip preserves DOUBLE+209 NULLs, DATE, boolean | integration | `tests/test_export.py::test_parquet_types -x` | ❌ Wave 0 |
| MODEL-04 | CSV reread preserves 209 NULLs (no 0-fill) | integration | `… ::test_csv_nulls -x` | ❌ Wave 0 |
| (regression) | Phase-1 null guard still green (209/4,405) | unit | `tests/test_nulls.py` (existing) | ✅ exists |

**Boundary test cases (parametrize like Phase 1 `test_rowcounts.py`):**
- `season`: month 12→Winter, 2→Winter, 3→Spring, 6→Summer, 8→Summer, 9→Fall, 11→Fall.
- `daypart`: hour 5→Night, 6→Morning, 10→Morning, 11→Midday, 14→Midday, 15→Afternoon/Evening, 19→Afternoon/Evening, 20→Night, 23→Night.
- `is_weekend`: a known Saturday/Sunday timestamp → true; a Wednesday → false.
- `fleet_age`: YEAR 2015→8, YEAR 1982→41, YEAR 2026→−3 (assert negatives allowed).

### Sampling Rate
- **Per task commit:** `uv run pytest -q tests/test_join_integrity.py` (the < 5s hard gate).
- **Per wave merge:** `uv run pytest -q` (full suite, includes Phase-1 regression guards).
- **Phase gate:** Full suite green before `/gsd:verify-work`; the join-integrity file is the non-negotiable gate (MODEL-03 is the flagship value-added measure).

### Wave 0 Gaps
- [ ] `tests/conftest.py` — add `gold` fixture that runs `transform.build_all(con)` + `model.build_all(con)` on the existing session `con`.
- [ ] `tests/test_join_integrity.py` — matched/unmatched/fan-out/unique-key/null-key asserts (MODEL-03).
- [ ] `tests/test_derived_fields.py` — parametrized fleet_age/season/daypart/dow/is_weekend/gap + ferry 15-min slot (MODEL-01).
- [ ] `tests/test_dimensions.py` — dim_date gapless, dim_time 96, dim_division conformed 21 (MODEL-02).
- [ ] `tests/test_export.py` — Parquet/CSV roundtrip type+null preservation (MODEL-04).
- [ ] (optional) `schemas.py` Gold-tier Pandera contracts (`fleet_age` int, `season`/`daypart` value sets) — nice-to-have, not gating.
- Framework install: none — pytest/pandera already in the dev group.

## Security Domain

> `security_enforcement` is not present in `.planning/config.json` (treated as enabled), but this phase has **no authentication, session, network, secret-handling, or untrusted-input surface**. It is a local, single-machine, read-only-CSV → local-Parquet data transform. The only inputs are three trusted City-of-Toronto CSVs already validated in Phase 1.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a — no auth surface |
| V3 Session Management | no | n/a — no sessions |
| V4 Access Control | no | n/a — local files only |
| V5 Input Validation | partial (data-integrity, not security) | Pandera schemas + row-count/null asserts (Phase 1) + Phase-2 join-integrity asserts; `read_csv`/`COPY` use DuckDB parameter binding (`?`) as in `ingest.py`, avoiding string-interpolated paths for user-supplied values |
| V6 Cryptography | no | n/a — no secrets/crypto |

### Known Threat Patterns for {DuckDB local ETL}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL built by f-string interpolation of external values | Tampering | Bind file paths/params with `?` (Phase 1 `ingest.py` does this); table names in `COPY` are internal constants from a `GOLD_TABLES` list, never user input. |
| Silent data corruption (a fill/cast altering audit numbers) | Tampering/Repudiation | The join-integrity + null-preservation tests are the integrity controls; full suite is the audit trail. |

## Sources

### Primary (HIGH confidence — live execution against the real codebase)
- `src/fleet_analytics/ingest.py`, `config.py`, `schemas.py`, `profile.py`, `__init__.py` — Phase-1 patterns reused/extended.
- `tests/conftest.py`, `tests/test_rowcounts.py`, `tests/test_nulls.py` — the `con` fixture + count-assertion pattern Phase 2 extends.
- Live DuckDB 1.5.3 execution (this session, 2026-06-02) against `bronze_availability`/`bronze_utilization`/`bronze_ferry`: verified avail non-numeric UNIT_NO == 44; util non-numeric == 0; matched == 2,080; unmatched == 6; fact_vehicle == 4,614; 0 dup keys; ferry 15-min 0 NaT / 272,529; dim_date 4,383 gapless; dim_time 96; dim_division union 21 (intersection 20); Parquet preserves DOUBLE+209 NULLs+DATE; CSV reread 209 nulls; `fleet_age` range −3…41.
- `uv run python -c "import duckdb,pandas,pyarrow; print(...)"` → 1.5.3 / 3.0.3 / 24.0.0.
- `pyproject.toml`, `.planning/config.json`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/PROJECT.md`, `.planning/STATE.md`, `02-CONTEXT.md`, `CLAUDE.md`.

### Secondary (MEDIUM confidence)
- CLAUDE.md "DuckDB-vs-pandas guidance" and "pytest patterns" tables — directly aligned with the verified patterns above.

### Tertiary (LOW confidence)
- None — all load-bearing claims were verified by live execution.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified by import on the installed env.
- Architecture / SQL patterns: HIGH — every snippet executed and reproduced the locked target numbers against real data.
- Pitfalls: HIGH — the 44-alnum-unit, negative-fleet_age, reserved-word, and `date_part`-quoting pitfalls were all triggered live and resolved.

**Research date:** 2026-06-02
**Valid until:** 2026-07-02 (30 days — stable in-process stack; the only volatility is a possible DuckDB minor bump, which would not change these patterns)
```
