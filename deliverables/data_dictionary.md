# Data Dictionary — Bronze Tables

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Layer:** Bronze (typed, as-ingested; no transforms applied)
**Generated from:** `src/fleet_analytics/profile.py::profile_facts` (DuckDB `SUMMARIZE` + targeted SQL)
**Snapshot pull date:** 2026-06-02 (the supplied files are treated as a point-in-time snapshot — see the [DQ report](dq_report.md), caveat A1)

This dictionary documents every column of the three Bronze tables exactly as they
are landed by `ingest_bronze(con)` — column name, DuckDB type as ingested,
nullability, and notes. Types are the explicit overrides from `config.py` for the
load-bearing columns and DuckDB-inferred for the rest. No imputation, no
re-typing, no derived columns appear here; those are Phase-2 work.

---

## 1. `bronze_availability` — City Vehicle Availability

**Source file:** `City Vehicle Availability .csv` (note the trailing space before `.csv` — preserved, not "fixed")
**Row count:** 4,614
**Portal status:** **Retired** — treat as a point-in-time YTD snapshot, not a live feed (caveat A1).

| Column | DuckDB type | Nullable | Notes |
|--------|-------------|----------|-------|
| `_id` | BIGINT | No | Open Data portal surrogate row id. |
| `UNIT_NO` | VARCHAR | No | Vehicle unit number; **zero-padded string** (e.g. `001052`) — kept VARCHAR so leading zeros survive. Normalization for the availability⋈utilization join is Phase 2. |
| `YEAR` | INTEGER | No | Model year. Range **1982 → 2026** (45 model years). |
| `MAKE` | VARCHAR | No | Manufacturer. |
| `MODEL` | VARCHAR | No | Model name. |
| `CATEGORY` | VARCHAR | No | Asset category code. |
| `CAT_DESC` | VARCHAR | No | Asset category description. |
| `UNIT_TYPE` | VARCHAR | No | Asset class (e.g. light-duty, heavy-duty, fire, etc.). |
| `CATEGORY_CLASS` | VARCHAR | No | Category class. **19 distinct values.** |
| `CAT_GRP` | VARCHAR | No | Category group. |
| `IN_SERV_DT` | DATE | No | In-service date — drives Phase-2 `fleet_age`. |
| `STATUS_DESC` | VARCHAR | No | Lifecycle status. **4 distinct values** (Active is the dominant ~4,195). |
| `CLASS2` | VARCHAR | No | Secondary class attribute. |
| `HIGH_PRIORITY` | VARCHAR | No | High-priority flag. |
| `OWNER_DIVISION` | VARCHAR | No | Owning City division. **21 distinct values.** May contain embedded commas (e.g. `"ENVIRONMENT, CLIMATE & FORESTR"`) — parsed via RFC-4180 quoting, not hand-split. |
| `REF_DIVISION` | VARCHAR | No | Reference division. |
| `SEASONAL` | VARCHAR | No | Seasonal flag (≈375 seasonal). |
| `AVAILABILITY_YTD` | DOUBLE | **Yes (209 nulls)** | Year-to-date availability as a **0–1 fraction**. Blank cells are landed as genuine SQL `NULL`, **never 0** — the 209 nulls (4.53%) are excluded from rate calcs, never imputed (DATA-03). 13 legitimate `0.0` values exist and are kept. Bounds: **min 0.0 / max 1.0**. Non-null denominator: **4,405**. |

---

## 2. `bronze_utilization` — Light-Duty City Vehicle Utilization

**Source file:** `Light duty city vehicle utilization data.csv`
**Row count:** 2,086

| Column | DuckDB type | Nullable | Notes |
|--------|-------------|----------|-------|
| `_id` | BIGINT | No | Open Data portal surrogate row id. |
| `UNIT_NO` | VARCHAR | No | Vehicle unit number; same zero-padded-string concern as availability. The join key to `bronze_availability` (Phase 2; target 2,080 matched / 6 unmatched). |
| `YEAR` | INTEGER | No | Model year. |
| `MAKE` | VARCHAR | No | Manufacturer. |
| `MODEL` | VARCHAR | No | Model name. |
| `Specialized units` | VARCHAR | No | Value set **{`Yes`, `No`}** (enforced by `schemas.py`). |
| `REF_USING_DIV` | VARCHAR | No | Using division reference. |
| `Utilization` | VARCHAR | No | **Pre-classified** label; value set **{`Underutilized`, `Not Underutilized`}** (enforced by `schemas.py`). **Not recomputed** — the classification is taken as supplied. 120 of 2,086 rows are `Underutilized` (5.75% ≈ 5.8%). |

---

## 3. `bronze_ferry` — Toronto Island Ferry Ticket Counts

**Source file:** `Toronto Island Ferry Ticket Counts.csv`
**Row count:** 272,529

| Column | DuckDB type | Nullable | Notes |
|--------|-------------|----------|-------|
| `_id` | BIGINT | No | Open Data portal surrogate row id. |
| `Timestamp` | TIMESTAMP | No | tz-naive. Range **2015-05-01 13:30 → 2026-06-01 22:30** (all 12 calendar years present). Drives Phase-2 season / daypart / day_of_week / is_weekend. |
| `Redemption Count` | BIGINT | No | Tickets redeemed in the interval. Median **11** / max **7,216** — heavy right skew (real peak windows). |
| `Sales Count` | BIGINT | No | Tickets sold in the interval. Median **12** / max **7,229** — heavy right skew (real peak windows, NOT an error). The Sales-vs-Redemption gap is surfaced for Phase-2 derivation and flagged for SME validation. |

---

## Conventions & Locked Decisions Reflected Here

- **`UNIT_NO` stays VARCHAR** in Bronze to preserve zero-padding (integer normalization is Phase 2).
- **`AVAILABILITY_YTD` stays DOUBLE and nullable** — 209 blanks are genuine `NULL`; exclude, never impute.
- **`Utilization` is taken pre-classified**, not recomputed.
- **Audit thresholds and the ~14% underutilization benchmark are cited, not recalculated** (see [DQ report](dq_report.md)).

## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets.
- **May 2023 FSD** General Government Committee report.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3**.
- Licence: **Open Government Licence – Toronto**.
