# Architecture Research

**Domain:** Analytics ETL (Python + DuckDB) feeding a hand-authored Power BI star-schema semantic model
**Researched:** 2026-06-01
**Confidence:** HIGH (Power BI star-schema, date/time-dimension, and relationship guidance verified against Microsoft Learn + SQLBI; medallion-lite ETL verified against current DuckDB practice)

## Standard Architecture

### System Overview

The pipeline is a small, reproducible, single-machine medallion-lite flow. Claude Code/GSD own everything up to and including the modeled tables + the KPI/measures spec. The Power BI canvas is authored by hand on top of the Gold output. Nothing in this architecture generates a `.pbix`/PBIP/TMDL.

```
┌──────────────────────────────────────────────────────────────────────┐
│  SOURCE (read-only)                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐   │
│  │ availability │  │ utilization  │  │ ferry ticket counts        │   │
│  │ 4,614 rows   │  │ 2,086 rows   │  │ 272,529 rows (15-min grain)│   │
│  └──────┬───────┘  └──────┬───────┘  └─────────────┬──────────────┘   │
├─────────┴─────────────────┴────────────────────────┴──────────────────┤
│  BRONZE / raw   (DuckDB: load CSV verbatim, typed, + row-count assert) │
│  raw_availability       raw_utilization        raw_ferry              │
├────────────────────────────────────────────────────────────────────── ┤
│  SILVER / cleaned  (normalize, parse, derive — one cleaned tbl/source) │
│  cln_availability       cln_utilization        cln_ferry              │
│   • normalize UNIT_NO     • normalize UNIT_NO    • parse Timestamp     │
│   • flag 209 nulls        • binary→flag          • round to 15-min     │
│   • derive fleet_age                             • derive gap          │
├──────────────────────────────────────────────────────────────────────┤
│  GOLD / modeled  (star schema — Power BI import target, Parquet/CSV)   │
│  ┌──────────────┐    ┌──────────────┐      ┌──────────────┐           │
│  │ dim_division │───<│ fact_vehicle │      │  fact_ferry  │>──┐       │
│  └──────────────┘    │ (=vehicle    │      └──────┬───────┘   │       │
│                      │  dim, 1 row  │             │           │       │
│                      │  per UNIT_NO)│      ┌──────┴─────┐  ┌──┴─────┐  │
│                      └──────────────┘      │  dim_date  │  │dim_time│  │
│                                            └────────────┘  └────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│  KPI / MEASURES SPEC  (SQL/Python validation values + DAX text spec)  │
│  kpi_definitions.md   measures_spec.md (copy-paste DAX)               │
├──────────────────────────────────────────────────────────────────────┤
│  REPORT SPEC + NARRATIVES  (hand-authored Power BI consumes these)    │
│  report_spec.md (page-by-page)   requirements.md   stakeholders.md    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Ingest (Bronze)** | Load 3 CSVs verbatim into DuckDB with explicit types; assert row counts (4,614 / 2,086 / 272,529); no transformation | `read_csv_auto` into DuckDB tables or a `raw/` Parquet drop |
| **Profile / DQ** | Nulls, ranges, outliers, cardinalities, the 5.8% vs 14% discrepancy; emit data dictionary + DQ report | DuckDB `SUMMARIZE` + pandas profiling; markdown output |
| **Transform (Silver)** | Normalize `UNIT_NO`; flag (not impute) 209 availability nulls; parse + round ferry timestamps to 15-min; derive fleet_age, season, daypart, dow, is_weekend, gap | SQL views/CTEs in DuckDB; pandas where convenient |
| **Model (Gold)** | Build `dim_division`, `fact_vehicle`, `fact_ferry`, `dim_date`, `dim_time`; run availability ⋈ utilization; export Parquet/CSV | DuckDB `CREATE TABLE AS` → `COPY ... TO ... (FORMAT parquet)` |
| **KPI / measures** | Compute every KPI in SQL/Python for validation; produce KPI definitions doc + DAX-ready measures spec | DuckDB aggregations + pytest bounds checks; markdown spec |
| **Report spec** | Page-by-page layout, slicer plan, theme, exact DAX, PDF-export layout | Markdown; hand-authored in Desktop from it |
| **Narratives** | Requirements-gathering approach + stakeholder-engagement strategy | Markdown drafts |
| **Power BI (manual)** | Import Gold Parquet, set relationships, Mark as Date Table, paste DAX, build canvas | Power BI Desktop — outside GSD scope |

## Recommended Project Structure

```
.
├── data/
│   ├── raw/                 # source CSVs (read-only, .gitignore'd or DVC'd)
│   ├── bronze/              # typed verbatim loads (optional persisted Parquet)
│   ├── silver/              # cleaned per-source tables
│   └── gold/                # star-schema Parquet — Power BI import target
│       ├── dim_division.parquet
│       ├── fact_vehicle.parquet
│       ├── fact_ferry.parquet
│       ├── dim_date.parquet
│       └── dim_time.parquet
├── src/
│   ├── ingest.py            # CSV → bronze, row-count asserts
│   ├── profile.py           # DQ report + data dictionary
│   ├── transform.py         # bronze → silver (normalize/parse/derive)
│   ├── model.py             # silver → gold (build star schema, the join)
│   └── kpis.py              # gold → KPI validation values
├── sql/                     # if SQL-first: one .sql per layer step
├── tests/
│   ├── test_ingest.py       # schema + row counts
│   ├── test_transform.py    # derived-field correctness, UNIT_NO normalization
│   ├── test_model.py        # join integrity (2,080/2,086), grain uniqueness
│   └── test_kpis.py         # KPI bounds vs audit benchmarks
├── specs/
│   ├── data_dictionary.md
│   ├── dq_report.md
│   ├── kpi_definitions.md
│   ├── measures_spec.md     # copy-paste DAX
│   └── report_spec.md       # page-by-page
├── docs/                    # requirements + stakeholder narratives, README
└── pipeline.py              # one-command orchestrator: ingest→profile→transform→model→kpis
```

### Structure Rationale

- **`data/{raw,bronze,silver,gold}/`:** Mirrors the medallion-lite layers physically so each step is inspectable and the pipeline is re-runnable from any layer. Gold is the contract handed to Power BI — keep it small, clean, and stable.
- **`src/` one module per layer step:** Matches the 6-phase roadmap so phase boundaries map onto files. Keeps the availability⋈utilization join isolated in `model.py` where the integrity test points.
- **`specs/` separate from `docs/`:** Specs are machine-adjacent (DAX text, KPI formulas Power BI consumes); docs are the human narrative deliverables. Both are first-class outputs, not afterthoughts.
- **`pipeline.py` orchestrator:** A single entry point makes the whole thing reproducible (and CI-able) without a heavyweight framework — appropriate at this scale.

## Architectural Patterns

### Pattern 1: Medallion-lite (raw → cleaned → modeled) on DuckDB

**What:** Three logical layers — Bronze (verbatim typed load), Silver (cleaned/conformed, one table per source), Gold (star-schema curated). DuckDB is the engine; Parquet is the on-disk contract.
**When to use:** Small, single-machine, reproducible analytics pipelines feeding BI. Exactly this project.
**Trade-offs:** Adds a little ceremony vs. one monolithic script, but buys reproducibility, testability per layer, and a clean Power BI import boundary. Do not over-build (no Delta/Iceberg, no orchestration engine, no warehouse) — that is enterprise-scale gold-plating for 280K rows.

**Example:**
```python
# Bronze: verbatim, asserted
con.sql("CREATE TABLE raw_ferry AS SELECT * FROM read_csv_auto('data/raw/ferry.csv')")
assert con.sql("SELECT count(*) FROM raw_ferry").fetchone()[0] == 272_529

# Gold: export contract for Power BI
con.sql("COPY fact_ferry TO 'data/gold/fact_ferry.parquet' (FORMAT parquet)")
```

### Pattern 2: Degenerate vehicle dimension (fact_vehicle doubles as dim)

**What:** Because availability and utilization are 1:1 per `UNIT_NO`, `fact_vehicle` carries both its measures (availability_ytd, utilization_status) AND its descriptive attributes (asset_class, make, model, model_year, fleet_age, flags). It is simultaneously the fact and the vehicle dimension.
**When to use:** When a fact's grain is one row per entity and there is no higher-cardinality event table for that entity. Idiomatic and correct here — splitting into `dim_vehicle` + `fact_vehicle` would be a 1:1 split that adds joins with zero analytical benefit.
**Trade-offs:** Slightly less "textbook pure," but Microsoft's own guidance treats 1:1 entity tables this way; a forced split is an anti-pattern at this grain. Keep `dim_division` separate (true 1-to-many lookup, drives a slicer).

**Example:**
```
dim_division (1) ──< fact_vehicle (many)
  division_key        division_key (FK)
  division_name       unit_no, asset_class, make, model, model_year,
  ...                 fleet_age_years, seasonal_flag, specialized_flag,
                      status, high_priority,
                      availability_ytd, is_underutilized   ← measures live here
```

### Pattern 3: Split date + time dimensions for sub-daily (15-min) grain

**What:** Never build one combined datetime dimension at 15-min grain (that is ~385K rows over 11 years and breaks DAX time intelligence). Instead split: `dim_date` = one row per **day** (4,000ish rows), `dim_time` = one row per **15-min slot within a day** (96 rows). `fact_ferry` carries two FKs: a `date` key and a `time` key, produced by rounding the parsed timestamp down to its 15-min slot.
**When to use:** Any fact below daily grain in Power BI. This is the verified Microsoft/RADACAD-recommended pattern.
**Trade-offs:** Requires splitting the timestamp during transform and rounding the fact to the slot boundary so the FK joins cleanly. In exchange you get working time intelligence (on the date side) AND clean intraday analysis (day-of-week × hour-of-day heatmap) from the 96-row time dim.

**Example:**
```
-- Silver/Gold: derive the two keys from one timestamp
date_key  = CAST(ts AS DATE)                              -- joins dim_date
time_key  = date_trunc('hour', ts)                        -- 15-min slot id
          + INTERVAL (floor(extract(minute FROM ts)/15)*15) MINUTE
-- store time_key as HH:MM or a 0..95 slot integer; dim_time has 96 rows
```

`dim_time` columns: `time_key`, `hour` (0–23), `minute_slot` (0/15/30/45), `slot_label` ("14:15"), `daypart` (overnight/AM peak/midday/PM peak/evening). `dim_date` columns: `date` (the key, `DATE` type), `year`, `quarter`, `month`, `month_name`, `day`, `day_of_week`, `day_name`, `is_weekend`, `season`.

### Pattern 4: KPI split — pre-compute structural values, leave additive/contextual to DAX

**What:** Decide per-KPI whether logic lives in the modeled tables (SQL/Python) or in DAX measures at report time.
**When to use:** Every KPI. The discriminating rule:
- **Goes in the model (row-level attributes/flags):** anything that is a per-row property — `fleet_age_years`, `season`, `daypart`, `is_weekend`, `sales_redemption_gap` (a row-level subtraction), `is_underutilized` flag, asset-class targets joined in as a column. These are dimensions/filters the user slices by; they must exist before report time.
- **Goes in DAX (aggregations that respond to slicer context):** `AVERAGE(availability_ytd)`, `gap-to-target = avg actual − target`, `% below threshold`, count of disposal candidates, ferry `SUM(sales)`/`SUM(redemption)`, YoY growth via `SAMEPERIODLASTYEAR`, the day-of-week × hour heatmap measure. These must recalculate as the user filters by division/asset-class/season/date — pre-aggregating them would freeze the numbers.
**Trade-offs:** Pre-aggregating KPIs in SQL is tempting and easy to validate, but it kills interactivity and is the classic "why doesn't my slicer work" failure. Keep facts at their natural grain (one row per vehicle; one row per 15-min slot) and express aggregations as DAX. Use the SQL/Python KPI values only to **validate** the DAX (the measures_spec carries both the formula and the expected number).

**Example:**
```
-- In model (row attribute, used as filter/axis):
fact_ferry.sales_redemption_gap = sales_count - redemption_count

-- In DAX spec (recalculates under slicer context):
Avg Availability := AVERAGE( fact_vehicle[availability_ytd] )    -- nulls auto-excluded
Gap to Target   := [Avg Availability] - SELECTEDVALUE( dim_target[target] )
Ferry YoY %     := DIVIDE([Tickets] - CALCULATE([Tickets], SAMEPERIODLASTYEAR(dim_date[date])),
                          CALCULATE([Tickets], SAMEPERIODLASTYEAR(dim_date[date])))
```

## Data Flow

### Pipeline flow (build-time, one-command)

```
3 CSVs
   ↓ ingest.py        (assert row counts → bronze)
bronze tables
   ↓ profile.py       (DQ report, data dictionary — does not block flow)
   ↓ transform.py     (normalize UNIT_NO, parse/round ts, derive fields → silver)
silver tables
   ↓ model.py         (build dims/facts, run availability⋈utilization → gold Parquet)
gold star schema  ──→  Power BI import (manual)
   ↓ kpis.py          (compute validation values → measures_spec numbers)
kpi/DAX specs     ──→  pasted into Power BI (manual)
```

### The availability ⋈ utilization join (the value-added measure)

```
cln_availability.UNIT_NO   (zero-padded string, e.g. "004821")
cln_utilization.UNIT_NO    (int, e.g. 4821)
        │
        ▼  normalize both: strip leading zeros / cast to a common type
        │  recommended: CAST(... AS BIGINT) on both sides (or TRIM/LTRIM '0')
        ▼
fact_vehicle  = availability LEFT JOIN utilization ON normalized UNIT_NO
        │
        ▼  EXPECT 2,080 of 2,086 utilization rows match
           → 6 unmatched is a documented DQ finding, not a bug
           → utilization columns are NULL for the ~2,528 vehicles
             not in the light-duty utilization file (correct: they were
             never classified). is_underutilized stays NULL/“n/a” for them.
```

Join integrity test (`test_model.py`) asserts: matched count == 2,080 (±documented), `fact_vehicle` grain is unique on UNIT_NO, and no utilization row silently duplicates an availability row (1:1 guarded).

### Power BI relationship model (set by hand from the spec)

```
dim_division ──(1:*, single-direction)──> fact_vehicle      filters flow dim→fact
dim_date     ──(1:*, single-direction)──> fact_ferry         Mark dim_date as Date Table
dim_time     ──(1:*, single-direction)──> fact_ferry
```

All relationships **single-direction**, **one-to-many** from dimension to fact (verified Microsoft + SQLBI guidance). `dim_date` uses a `DATE`-typed key column and is set via *Modeling → Mark as Date Table* so TOTALYTD/SAMEPERIODLASTYEAR/PARALLELPERIOD work. No bidirectional filtering. The two facts share no relationship (different domains) — correct; do not try to bridge them.

### Key data flows

1. **Fleet KPI flow:** slicer (division/asset-class/season) → filters `fact_vehicle` via `dim_division` and its own attribute columns → DAX measures aggregate availability/utilization under that context → cards, gap-to-target bars, exception list (drill-through on units below threshold).
2. **Ferry KPI flow:** date slicer → `dim_date` filters `fact_ferry`; `dim_time` provides the intraday axis → DAX SUM/time-intelligence measures → YoY trend, seasonal profile, day-of-week × hour heatmap (matrix of `dim_date[day_name]` × `dim_time[hour]` over `SUM(sales)`).

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| This project (280K rows, single machine) | DuckDB + Parquet is overkill-proof; runs in seconds. No changes needed. |
| 10× ferry data (multi-route, multi-year) | Still single-machine DuckDB. Partition gold Parquet by year if import slows; consider DirectQuery only if data outgrows import memory. |
| Recurring refresh / scheduled | Add a thin orchestrator (the existing `pipeline.py`, optionally GitHub Actions cron) and incremental loads; the layer structure already supports it. |

### Scaling priorities

1. **First "bottleneck" is human, not machine:** the risk is model correctness (join integrity, grain, relationship direction), not performance. Invest tests there.
2. **If Power BI import ever slows:** narrow gold tables (drop unused columns), keep `dim_time` at 96 rows, and ensure FK columns are integers/dates for VertiPaq compression — not a concern at current size.

## Anti-Patterns

### Anti-Pattern 1: Combined 15-min datetime dimension

**What people do:** One `dim_datetime` with a row per 15-min interval across 11 years (~385K rows).
**Why it's wrong:** Bloats the model, can't be cleanly Marked as Date Table, and DAX time-intelligence functions expect a contiguous **daily** date table.
**Do this instead:** Split into `dim_date` (per day) + `dim_time` (96 rows). Round the fact timestamp to its slot and carry two FKs.

### Anti-Pattern 2: Pre-aggregating KPIs into the model

**What people do:** Build a SQL table of "availability by asset class" and import that as the fact.
**Why it's wrong:** Freezes the numbers — slicers stop working, drill-through dies, and the value-added cross-measures (disposal candidates) can't be composed interactively.
**Do this instead:** Keep facts at natural grain; express aggregations as DAX measures. Use SQL KPI outputs only to validate the DAX in the measures spec.

### Anti-Pattern 3: Bidirectional or many-to-many relationships

**What people do:** Set relationships to "Both" to "make filtering work."
**Why it's wrong:** Performance hits, ambiguous filter propagation, hard-to-debug results.
**Do this instead:** Single-direction, one-to-many dim→fact. If a cross-filter is genuinely needed, use a measure with `CROSSFILTER`/`TREATAS` rather than changing the relationship.

### Anti-Pattern 4: Imputing the 209 availability nulls

**What people do:** Fill nulls with the mean to "complete" the data.
**Why it's wrong:** Distorts audit-benchmarked rates; indefensible in a BA review. (Also a project Key Decision.)
**Do this instead:** Exclude from rate calcs (DAX `AVERAGE` ignores blanks natively) and surface the 4.5% gap as a documented DQ finding.

### Anti-Pattern 5: Forcing a separate dim_vehicle

**What people do:** Split `fact_vehicle` into `dim_vehicle` + `fact_vehicle` for "purity."
**Why it's wrong:** Availability/utilization are 1:1 per unit — the split adds a join with no benefit.
**Do this instead:** Keep the degenerate/enriched `fact_vehicle` (Pattern 2).

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Power BI Desktop | Import gold Parquet from `data/gold/` | Manual; GSD never opens/writes the `.pbix`. Relationships, Mark as Date Table, and DAX are set by hand from `specs/`. |
| GitHub Actions (optional) | Run `pipeline.py` + pytest on push | Reproducibility/CI; not required for grading. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Silver ↔ Gold | DuckDB tables → Parquet files | Gold Parquet is the stable contract; downstream depends only on it. |
| Model ↔ KPI spec | SQL KPI values → measures_spec numbers | Validation values pair with DAX text; keeps DAX honest. |
| KPI spec ↔ Power BI | Markdown DAX → manual paste | One-way; spec is source of truth for measures. |

## Build Order (maps to the brief's 6 phases)

The pipeline layers and the brief's phases line up one-to-one — build strictly in this order because each layer is the input contract for the next.

| Phase | Builds | Depends on | Hard gate before moving on |
|-------|--------|-----------|----------------------------|
| **1 — Ingest, profile, DQ** | bronze loads + DQ report + data dictionary | source CSVs | row-count + schema tests pass |
| **2 — Transform & model** | silver cleaning + gold star schema + the join | Phase 1 bronze | join integrity (2,080/2,086), derived-field tests, grain uniqueness |
| **3 — KPI / measures layer** | SQL/Python KPI values + KPI defs doc + DAX measures spec | Phase 2 gold | KPI bounds/sanity vs audit benchmarks |
| **4 — Power BI delivery spec** | page-by-page report spec, slicer plan, theme, PDF layout | Phase 3 specs | spec references real measures + gold columns |
| **5 — Narratives** | requirements + stakeholder drafts | brief/audit context | (parallelizable with 4) |
| **6 — Ship** | PDF, README, citations, packaging | all prior | three components complete |

**Dependency notes:**
- Phases 1→2→3 are strictly sequential (data contracts).
- Phase 4 depends on 3 (the report spec cites exact measure names from measures_spec).
- Phase 5 (narratives) is independent of the data layer and can run in parallel with 3/4.
- The 15-min split and UNIT_NO normalization both land in Phase 2 — they are the highest-risk transforms and where the integrity tests concentrate.

## Sources

- [Understand star schema and the importance for Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) — HIGH
- [Design guidance for date tables in Power BI — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables) — HIGH
- [Set and use date tables in Power BI Desktop (Mark as Date Table) — Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-date-tables) — HIGH
- [How to Use Time and Date Dimensions in a Power BI Model — RADACAD](https://radacad.com/how-to-use-time-and-date-dimensions-in-a-power-bi-model/) — MEDIUM (sub-daily split + round-to-interval pattern)
- [Choosing between Date or Integer to represent dates — SQLBI](https://www.sqlbi.com/articles/choosing-between-date-or-integer-to-represent-dates-in-power-bi-and-tabular/) — HIGH (date-typed key, no perf penalty)
- [Power BI — Star schema or single table — SQLBI](https://www.sqlbi.com/articles/power-bi-star-schema-or-single-table/) — HIGH (degenerate-dim justification)
- [DuckDB Medallion Architecture: A Complete Local Lakehouse Guide — Medium/datatomas](https://medium.com/@datatomas/duckdb-medallion-architecture-a-complete-local-lakehouse-guide-0f1944b6bcdf) — MEDIUM (bronze/silver/gold on DuckDB+Parquet)
- City of Toronto FSD brief + PROJECT.md (this repo) — project-specific constraints

---
*Architecture research for: analytics ETL + Power BI dimensional model (City of Toronto Fleet/Ferry)*
*Researched: 2026-06-01*
