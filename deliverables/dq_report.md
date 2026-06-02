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

## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets.
- **May 2023 FSD** General Government Committee report.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3** (the ~14% underutilization benchmark and downtime themes).
- Licence: **Open Government Licence – Toronto**.

*All computed figures reproducible via `profile_facts(con)`; locked by `tests/test_profile.py`.*
