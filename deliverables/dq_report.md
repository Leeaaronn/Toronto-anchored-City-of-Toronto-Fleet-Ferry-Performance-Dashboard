# Data Quality Report — Phase 1 Baseline (DATA-02)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** Bronze tables (as-ingested, pre-transform) for the three source datasets.
**Method:** All figures are computed deterministically by `src/fleet_analytics/profile.py::profile_facts`
using DuckDB `SUMMARIZE` + targeted SQL — **not** a profiling-library HTML (that path is
optional and intentionally skipped for a reproducible, citable baseline). Every headline
number below is locked by `tests/test_profile.py`.
**Snapshot pull date:** **2026-06-02** (see caveat A1).

> **Why this report exists.** Per the Phase-1 goal, every data-quality fact is documented as a
> **stated assumption before any transform is written**. Two figures here are *cited narrative
> facts, not computed*: the availability dataset's retired/snapshot status (A1) and the AG's
> ~14% underutilization benchmark (A2). They are flagged inline so the downstream dashboard
> claims remain audit-defensible.

---

## 1. Row Counts (DATA-01)

| Table | Rows | Status |
|-------|------|--------|
| `bronze_availability` | **4,614** | Matches expected — fail-fast guard green. |
| `bronze_utilization` | **2,086** | Matches expected. |
| `bronze_ferry` | **272,529** | Matches expected. |

Row counts are asserted at ingest (`ingest_bronze`) so a re-supplied or truncated CSV fails immediately.

---

## 2. `AVAILABILITY_YTD` — Nulls & Range (DATA-03)

| Metric | Value |
|--------|-------|
| Non-null rows (rate denominator) | **4,405** |
| **Null rows** | **209 (4.53%)** |
| Min | **0.0** |
| Max | **1.0** |

- The 209 nulls are landed as genuine SQL `NULL` (the column is `DOUBLE`, never `COALESCE`'d).
  **Locked decision: exclude, never impute** — all availability rates use the **4,405** denominator,
  because imputing would distort the audit-benchmarked rates.
- There are **13 legitimate `0.0`** availability values; these are real (a vehicle truly at 0%
  availability), kept distinct from the 209 missing values. The regression guard is that the
  non-null count stays exactly 4,405 (a silent fill would push it toward 4,614).
- Values are bounded to **[0, 1]** as a 0–1 fraction; enforced by the Pandera contract in `schemas.py`.

---

## 3. Ferry Ticket Counts — Right-Skew Story (NOT an error)

| Series | Median | Max |
|--------|--------|-----|
| `Sales Count` | **12** | **7,229** |
| `Redemption Count` | **11** | **7,216** |

The distance between the median (~12) and the max (~7,229) is **heavy right skew driven by real
peak windows** — summer weekends, holidays, and festival days at the Toronto Island ferry docks.
**This is a genuine outlier story, not a data error**: most 15-/30-minute intervals are quiet, while
a handful of peak intervals move thousands of tickets. The Sales-vs-Redemption gap (median 12 vs 11)
is surfaced for Phase-2 derivation (`sales_redemption_gap`) and **flagged for SME validation** —
the exact business meaning of "sales" vs "redemption" is an assumption to confirm.

The full timestamp span is **2015-05-01 → 2026-06-01** with all 12 calendar years present, supporting
the planned YoY and seasonality analysis (including the expected 2020–21 pandemic dip).

---

## 4. Categorical Domains

| Field | Distinct values |
|-------|-----------------|
| `OWNER_DIVISION` (availability) | **21** |
| `CATEGORY_CLASS` (availability) | **19** |
| `STATUS_DESC` (availability) | **4** |
| `Utilization` (utilization) | **2** — {`Underutilized`, `Not Underutilized`} |
| `Specialized units` (utilization) | **2** — {`Yes`, `No`} |
| `YEAR` (availability) | range **1982 → 2026** |

Value sets for `Utilization` and `Specialized units` are enforced as Pandera contracts (`schemas.py`).

---

## 5. Underutilization: 5.8% (CSV) vs ~14% (Audit) — a Stated Insight

| Measure | Value | Source |
|---------|-------|--------|
| Underutilized (this CSV) | **120 / 2,086 = 5.75% ≈ 5.8%** | **Computed** here from `bronze_utilization`. |
| Underutilization benchmark | **~14%** | **Cited** — Auditor General **Operational Review 2019.AU2.3** (caveat A2). |

**Framing (A2 — cited, not computed).** The light-duty utilization file classifies **5.8%** of units as
`Underutilized`, materially **lower** than the **~14%** figure highlighted in the AG's 2019 Operational
Review (2019.AU2.3). This gap is presented as a **period / right-sizing insight, NOT an error**:

- The two figures cover **different periods and potentially different scoping** (the supplied CSV is a
  later light-duty snapshot; the AG figure is the 2019 review baseline).
- A plausible reading is that **right-sizing actions taken after the 2019 audit reduced measured
  underutilization** — i.e. the gap is evidence of progress, not a contradiction.
- The classification is **taken as supplied and not recomputed**; the ~14% benchmark is a **cited
  narrative fact from the AG report**, not derivable from the CSV.

This contrast is a headline talking point for the dashboard and panel interview, surfaced with its
provenance attached so it remains defensible.

---

## 6. Stated Caveats (Assumptions Log)

| ID | Caveat | Disposition |
|----|--------|-------------|
| **A1** | The City Vehicle Availability dataset is listed **Retired** on the Open Data portal. The supplied file is therefore treated as a **point-in-time YTD snapshot**, not a live feed. **Recorded snapshot pull date: 2026-06-02.** | **Cited**, not computed. Any availability rate is "as of the snapshot," not current. |
| **A2** | The **~14% underutilization** benchmark is from the **AG 2019.AU2.3 Operational Review**, not derivable from the CSV. | **Cited** inline (§5). |
| **A3** | The Sales-vs-Redemption interpretation for the ferry data is an assumption. | Flagged for **SME validation** (§3). |

---

---

# Phase-2 Addendum — Model & Join-Integrity DQ Findings

**Scope:** Gold star-schema build (the availability ⋈ utilization join and the conformed
`dim_division`). These findings emerge only once the two vehicle datasets are normalized to a
canonical integer key and joined — they extend, and do not revise, the Phase-1 baseline above.
**Method:** computed deterministically in `src/fleet_analytics/model.py` and locked by
`tests/test_join_integrity.py` / `tests/test_dimensions.py`. Every count below is a passing
test assertion, not a narrative estimate.

## 7. The 6 Unmatched Utilization Rows (D-03)

| Measure | Value |
|---------|-------|
| Utilization rows total | **2,086** |
| Matched to availability (canonical integer `UNIT_NO`) | **2,080** |
| **Unmatched (no availability row)** | **6** |
| Reconciliation | **2,080 + 6 = 2,086** ✓ |

The light-duty utilization file carries **6 `UNIT_NO` values with no corresponding availability
record**. They are surfaced by an **anti-join** (`bronze_utilization LEFT JOIN bronze_availability …
WHERE availability IS NULL`), materialized as the `dq_unmatched_utilization` table, and guarded by
`test_unmatched_6` (asserts the count is exactly 6).

These 6 rows **fall outside `fact_vehicle` by design.** `fact_vehicle` is **availability-anchored**
(all 4,614 availability rows, LEFT JOIN to utilization), so a utilization record with no availability
match has no row to attach to — that is expected, not an error. The anti-join is the deliberate
capture point so the discrepancy is documented and testable rather than silently dropped. The join
itself does **not** fan out: `fact_vehicle` stays exactly **4,614** rows.

## 8. The 44 Alphanumeric Availability `UNIT_NO` Values

| Measure | Value |
|---------|-------|
| Availability rows total | **4,614** |
| Availability units with a non-integer (alphanumeric) `UNIT_NO` | **44** (e.g. `296011A`, `CLAW10`) |
| Their canonical integer join key (`unit_key_int`) | **NULL — by design** |

`UNIT_NO` is normalized to a canonical integer key via **`TRY_CAST(UNIT_NO AS BIGINT)`** on both
datasets. **44 availability units carry alphanumeric IDs** (e.g. `296011A`, `CLAW10`) that are not
valid integers; `TRY_CAST` yields **NULL** for them rather than raising — so the rows **survive in
`fact_vehicle`** with a NULL `unit_key_int` and simply **never match** the integer-keyed utilization
side. This is the deliberate, defensible behavior: these are **real fleet units** and must remain in
the full-fleet availability denominator and the availability-by-asset-class measures; they are merely
**excluded from the integer join key** (utilization is light-duty only, so a non-light-duty
alphanumeric unit would have no utilization match regardless). No spelling is "fixed" and no row is
dropped — the alphanumeric IDs are preserved verbatim.

## 9. Division-Name Reconciliation (D-06) — a Clean Result

| Source role | Distinct normalized names |
|-------------|---------------------------|
| `OWNER_DIVISION` (availability — *owns* the vehicle) | **21** |
| `REF_USING_DIV` (utilization — *uses* the vehicle) | **20** |
| Conformed `dim_division` (distinct **union**, normalized) | **21** |
| Unreconciled names (in one source, absent from the other after normalization) | **0** |

`dim_division` is built as the **distinct union of normalized** (`trim` + collapse internal
whitespace + uppercase) division names from both sources — spellings are **not** force-mapped. The
union is **exactly 21 = the owner count**, because all **20** using-division names are a **normalized
subset** of the **21** owner names. The result is therefore **clean: zero unreconciled names** — every
using division also appears as an owner division. `dim_division` row count == **21** is locked by
`test_dimensions.py`.

Note the **source truncations are preserved verbatim, not "fixed."** `OWNER_DIVISION` arrives
truncated in the source CSV — e.g. **`ENVIRONMENT, CLIMATE & FORESTR`** (the trailing `Y` is cut off
upstream). We keep it as-is and document the truncation rather than guessing the full name; the
embedded comma parses correctly because Bronze ingest uses RFC-4180 CSV quoting (no hand-splitting).

---

## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets.
- **May 2023 FSD** General Government Committee report.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3** (the ~14% underutilization benchmark and downtime themes).
- Licence: **Open Government Licence – Toronto**.

*Phase-1 computed figures reproducible via `profile_facts(con)`; locked by `tests/test_profile.py`.
Phase-2 join/reconciliation figures locked by `tests/test_join_integrity.py` and `tests/test_dimensions.py`.*
