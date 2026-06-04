# KPI Definitions — Phase 3 KPI Layer (KPI-02)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** Every Domain A (fleet maintenance) and Domain B (Toronto Island Ferry) KPI computed authoritatively over the Phase-2 Gold star schema (`data/gold/*.parquet`), cross-checked against audit benchmarks.
**Method:** All headline figures are computed deterministically by `src/fleet_analytics/kpis.py` (DuckDB SQL-first, one builder per KPI) and persisted to the committed snapshot `data/kpi/kpi_values.json` + seven per-table CSVs. Every number below is **transcribed from that snapshot, not re-estimated**; the snapshot is locked by `tests/test_kpis.py`. Audit benchmarks (asset-class targets, the ~14% underutilization figure) are **cited, never recalculated**.
**Snapshot pull date:** **2026-06-02** (the supplied availability file is a point-in-time YTD snapshot — see the [DQ report](dq_report.md), caveat A1).

> **Why this doc exists.** This is the panel-ready, plain-language companion to the build contract in [`measures_spec.md`](measures_spec.md). It states the formula and audit benchmark for every KPI, distinguishes **computed** figures from **cited** audit facts inline (exactly as the [DQ report](dq_report.md) does), carries the **5.8%-computed vs ~14%-cited** underutilization reconciliation, and maps each KPI to the Auditor General theme it serves (downtime **2019.AU2.2** / underutilization **2019.AU2.3**). Two locked framings recur: availability rates **exclude the 209 NULL `AVAILABILITY_YTD` values** (denominator **4,405**, never imputed), and the disposal-candidate cross-measure is a **screening list for SME review, never a disposal decision**.

---

# Domain A — Fleet Maintenance KPIs

## 1. Overall Availability Rate (pooled per-vehicle mean)

**Plain-language formula.** The overall availability rate is the **pooled mean of `AVAILABILITY_YTD` across every non-null vehicle** — `SUM(AVAILABILITY_YTD) ÷ COUNT(non-null rows)`. It is **NOT** the average of the per-class averages; pooling weights each vehicle equally, so larger classes pull the grand total toward their own rate.

| Measure | Value | Source |
|---------|-------|--------|
| Overall availability rate (pooled) | **0.8899 ≈ 89.0%** | **Computed** — `AVG(AVAILABILITY_YTD)` over 4,405 non-null rows. |
| Non-null denominator | **4,405** | **Computed** — the 209 NULLs are excluded, never imputed. |
| NULL rows excluded | **209** | **Computed** — landed as genuine SQL `NULL` (DQ report §2). |
| Mean-of-class-means (the WRONG grand total) | **0.8786** | **Computed** — stored only to prove pooled ≠ average-of-averages. |

The pooled mean (**0.8899**) and the mean-of-class-means (**0.8786**) genuinely differ by ~0.011; the compute layer and `tests/test_kpis.py` assert they differ so an `AVERAGEX`-over-class-averages regression fails loudly. The **209-NULL exclusion** (denominator **4,405**) is the load-bearing rule for every availability rate in this doc.

## 2. Availability by Asset Class vs Audit Target (signed gap-to-target)

**Plain-language formula.** For each asset class, the **pooled availability rate** (per KPI 1, NULLs excluded) is compared to the **audit-cited class target**. `gap_to_target = actual − (target ÷ 100)` is **signed** — negative means below the benchmark (D-03). The targets are **cited from the AG 2019.AU2.2 downtime review / May 2023 FSD report and are never recalculated**.

| Asset class | Pooled availability rate (computed) | Audit target (cited) | Signed gap-to-target (computed) | Below-target units (computed) |
|-------------|------------------------------------|----------------------|---------------------------------|-------------------------------|
| Light | **0.9149 ≈ 91.5%** | **95** | **−0.0351** | 877 of 2,101 |
| Medium | **0.8612 ≈ 86.1%** | **92** | **−0.0588** | 297 of 607 |
| Heavy | **0.7948 ≈ 79.5%** | **85** | **−0.0552** | 275 of 588 |
| Off-Road | **0.8882 ≈ 88.8%** | **88** | **+0.0082** | 175 of 608 |
| Other | **0.9337 ≈ 93.4%** | **90** | **+0.0337** | 110 of 501 |

A unit is **"below threshold" when `AVAILABILITY_YTD < its class target`** — class-fair: a heavy-duty unit is judged against the 85 bar, not the 95 light-duty bar (D-01). This one threshold rule drives the exception list (KPI 3) and the disposal screen (KPI 5). **Light, Medium, and Heavy sit below their audit targets**; Off-Road and Other clear theirs.

## 3. Exception List — Critically-Low Units

**Plain-language formula.** The named list of every unit whose `AVAILABILITY_YTD` is **below its own asset-class target** (the same D-01 rule as KPI 2), ranked ascending by signed `gap_to_target` (worst first). Each row carries `unit_no`, `unit_type`, `asset_class`, `availability_ytd`, `target`, the signed gap, and the `Utilization` flag.

| Measure | Value | Source |
|---------|-------|--------|
| Units below their class target | **1,734** | **Computed** — `data/kpi/exception_list.csv`. |

This is the operational drill-down for the downtime theme (AG 2019.AU2.2): the worst-availability units, surfaced by name for maintenance triage. NULL-availability rows are excluded by the strict `<` comparison (consistent with the 209-NULL exclusion).

## 4. Underutilization Rate — Overall, by Using Division, Specialized Split

**Plain-language formula.** The share of **matched light-duty units** flagged `Utilization = 'Underutilized'` — `COUNT(Underutilized) ÷ COUNT(light-duty rows with a utilization flag)`. The classification is **pre-applied in the supplied data and taken as-is, never recomputed**. Computed overall, by **using** division, and with a specialized-units share alongside.

| Measure | Value | Source |
|---------|-------|--------|
| Overall underutilization rate | **0.0572 ≈ 5.8%** | **Computed** — over 2,080 matched light-duty units. |
| Matched light-duty denominator | **2,080** | **Computed** — the availability⋈utilization join (DQ report §7). |

By-division detail lives in `data/kpi/underutilization_by_division.csv` (e.g. **Facilities Mgmt & Real Estate 9.4%**, **Parks & Recreation 8.9%**, **Toronto Water 7.3%**), each row carrying a specialized-units share. Underutilization is the AG 2019.AU2.3 theme.

## 5. Disposal-Candidate Cross-Measure (SME screening list)

**Plain-language formula.** A unit is a disposal **candidate** when it is **below its class target** (the D-01 rule) **AND** pre-classified **`Underutilized`** (D-02). One threshold rule, no second floor — the same bar feeds the exception list, the "% below threshold" metric, and this screen.

| Measure | Value | Source |
|---------|-------|--------|
| Disposal candidates (below-target **AND** Underutilized) | **34** | **Computed** — `disposal_candidate = true` rows in `exception_list.csv`. |

**This is a screening list for SME review, not a disposal decision.** It flags 34 units that warrant a human right-sizing conversation; it does not recommend disposal. The framing is deliberate — the value of the value-added availability⋈utilization join is surfacing this short, defensible SME shortlist, never automating a fleet decision.

## A-Reconciliation. Underutilization: 5.8% (computed) vs ~14% (cited audit)

The KPI-layer underutilization rate (**5.8%**, computed here over the matched light-duty subset) is materially **lower** than the **~14%** figure in the AG's **2019 Operational Review (2019.AU2.3)**. This **extends and cross-references the existing reconciliation table at [`dq_report.md`](dq_report.md) §5 (the "5.8% vs ~14%" insight)** — the thresholds there are **cited, not recomputed**.

| Measure | Value | Source |
|---------|-------|--------|
| Underutilization (this KPI layer) | **≈ 5.8%** | **Computed** — KPI 4 above. |
| Underutilization benchmark | **~14%** | **Cited** — AG **Operational Review 2019.AU2.3** (audit Mar-2023 framing). |

The two figures cover **different periods and scoping** (the supplied CSV is a later light-duty snapshot; the AG figure is the 2019 baseline). A plausible, defensible reading is that **right-sizing after the 2019 audit reduced measured underutilization** — the gap is evidence of progress, not a contradiction. The classification is taken as supplied; the **~14%** is a cited narrative fact, not derivable from the CSV. See the [DQ report](dq_report.md) §5 for the full provenance.

---

# Domain B — Toronto Island Ferry KPIs

## 6. Lifetime / Period Totals (ALL data)

**Plain-language formula.** Sum of `Sales Count` and `Redemption Count` across **every 15-minute interval in the full span** (May 2015 → Jun 2026) — lifetime totals use **all** data (D-09), partial years included.

| Measure | Value | Source |
|---------|-------|--------|
| Lifetime ticket sales | **13,257,804** | **Computed** — `SUM("Sales Count")` over all rows. |
| Lifetime ticket redemptions | **13,076,317** | **Computed** — `SUM("Redemption Count")` over all rows. |

## 7. Year-over-Year Trend (complete years 2016–2025 only)

**Plain-language formula.** Annual `Sales`/`Redemption` totals with YoY growth via a `LAG` window — computed **only on the complete calendar years 2016–2025** (D-10). The partial **2015** (~8 months) and **2026** (~6 months) years are **labeled partial and excluded** from the YoY growth rows so endpoints do not distort the trend.

| Year | Ferry sales (computed) | Note |
|------|------------------------|------|
| 2019 | **1,249,725** | Pre-pandemic baseline. |
| 2020 | **366,606** | **COVID dip — 2020 < 2019** (asserted by the compute guard and `tests/test_kpis.py`). |

The full series lives in `data/kpi/ferry_yoy.csv` (2016–2025); the **2020 < 2019** COVID dip is a locked regression guard. 2015 and 2026 are partial and excluded from YoY.

## 8. Seasonality Profile (pool all years by month)

**Plain-language formula.** Monthly `Sales`/`Redemption` totals **pooling every year by calendar month** (and the Phase-2 `season` derived field) — **no annualization or partial-year estimation** (D-11). Every month of data contributes once, keeping the framing audit-grounded and assumption-free. Detail in `data/kpi/ferry_seasonality` (summer peaks dominate the Toronto Island docks).

## 9. Day-of-Week × Hour-of-Day Heatmap (ALL data)

**Plain-language formula.** `Sales`/`Redemption` demand grouped by the Phase-2 `day_of_week` derived field × `hour(Timestamp)`, long-form, over **all** data (D-09). Detail in `data/kpi/ferry_heatmap.csv`; orientation (DoW × hour) is a Phase-4 presentation choice.

## 10. Sales-to-Redemption Gap (signed)

**Plain-language formula.** The Phase-2 signed `sales_redemption_gap` derived field (`Sales − Redemption`, **never `abs()`**), aggregated per complete year. Positive = more sold than redeemed in the period.

| Measure | Value | Source |
|---------|-------|--------|
| 2016 total signed gap | **+92,649** | **Computed** — `data/kpi/sales_redemption_gap.csv`. |
| 2020 total signed gap | **−7,940** | **Computed** — same file. |

The interpretation of "sales" vs "redemption" is an **assumption flagged for SME validation** (DQ report caveat A3); the gap is surfaced, not adjudicated.

## 11. Distribution Stats (right-skew story)

**Plain-language formula.** Central-tendency and peak of `Sales Count` per 15-minute interval — the median vs max distance is **heavy right skew driven by real peak windows** (summer weekends, holidays), **not a data error**.

| Measure | Value | Source |
|---------|-------|--------|
| `Sales Count` median | **12** | **Computed** — `median("Sales Count")`. |
| `Sales Count` max | **7,229** | **Computed** — `MAX("Sales Count")`. |

The median (**12**) vs max (**7,229**) gap is the genuine outlier story; `ferry_sales_max == 7229` is a locked distribution guard.

---

## KPI ↔ AG Theme Traceability

Every KPI traces to an Auditor General Operational Review theme: **downtime/availability → 2019.AU2.2**; **underutilization → 2019.AU2.3**. Ferry KPIs are operational-demand context (no direct AG fleet theme), supporting the broader Fleet Services analytics narrative.

| KPI | Domain | AG Theme |
|-----|--------|----------|
| 1. Overall availability rate (pooled) | A | **AU2.2** (downtime / availability) |
| 2. Availability by class vs target | A | **AU2.2** (downtime / availability) |
| 3. Exception list (critically-low units) | A | **AU2.2** (downtime / availability) |
| 4. Underutilization rate (overall / by division / specialized) | A | **AU2.3** (underutilization) |
| 5. Disposal-candidate SME screening list | A | **AU2.2 + AU2.3** (low availability **and** underutilized) |
| 6–11. Ferry totals / YoY / seasonality / heatmap / gap / distribution | B | Operational demand context (no direct AG fleet theme) |

---

## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets.
- **May 2023 FSD** General Government Committee report.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3** (the ~14% underutilization benchmark and downtime themes).
- Licence: **Open Government Licence – Toronto**.

*KPI figures are computed by `src/fleet_analytics/kpis.py`, persisted to `data/kpi/kpi_values.json` + the seven per-table CSVs, and locked by `tests/test_kpis.py`. Audit thresholds are cited, never recalculated.*
