# DAX Measures Spec — Phase 3 Build Contract (KPI-02)

**Project:** Fleet Services Analytics — City of Toronto BA Assignment
**Scope:** The Phase-4 build contract — copy-paste DAX for every Domain A (fleet maintenance) and Domain B (ferry) KPI, each paired with the **SQL validation value** it must reproduce.
**Method:** Every "SQL validation value" cell **transcribes a value persisted in the committed snapshot** `data/kpi/kpi_values.json` or the relevant per-table CSV — values are **not** invented or re-estimated. The snapshot is computed by `src/fleet_analytics/kpis.py` and locked by `tests/test_kpis.py`. When the user wires these measures in Power BI against the Gold Parquet, every measure is **falsifiable**: it must reproduce its validation value. This doc is the companion to the plain-language [`kpi_definitions.md`](kpi_definitions.md); measure semantics are kept consistent between the two.
**Snapshot pull date:** **2026-06-02** (point-in-time availability snapshot — see [DQ report](dq_report.md), caveat A1).

> **How to read this spec.** Grouped **domain → KPI**: a Fleet Maintenance section and a Ferry section, each KPI a subsection with a `Measure name | DAX | SQL validation value | Notes` table. **Scope split (locked):** GSD produces this **text spec**; the Power BI report canvas, relationships, and theme are authored manually in Phase 4 — **no `.pbix` / PBIP / TMDL is generated here.** DAX measure names are Power-BI-friendly suggestions (planner discretion); the user may rename, but the SQL validation value is the binding contract. All availability measures **exclude the 209 NULL `AVAILABILITY_YTD` values** (`DIVIDE`/`AVERAGE` ignore blanks; denominator 4,405). Ratios use `DIVIDE` for safe division.

---

## Fleet Maintenance (Domain A)

### A1. Overall Availability Rate (pooled per-vehicle mean)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Availability Rate (Pooled)` | `Availability Rate (Pooled) = DIVIDE ( SUM ( fact_vehicle[AVAILABILITY_YTD] ), COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) ) ) )` | **0.8899** (`overall_availability_rate` = 0.8899126467628139) | **Pooled grand-total form — NOT `AVERAGEX` over class averages.** `DIVIDE(SUM, COUNTROWS over non-null)` weights each vehicle equally. The 209 NULLs are excluded (denominator 4,405); `SUM`/`COUNTROWS(FILTER NOT ISBLANK)` ignore blanks, never impute. |
| `Mean of Class Means (guard only)` | `Mean of Class Means = AVERAGEX ( VALUES ( fact_vehicle[UNIT_TYPE] ), CALCULATE ( AVERAGE ( fact_vehicle[AVAILABILITY_YTD] ) ) )` | **0.8786** (`mean_of_class_means` = 0.8785521577) | The **WRONG** grand total — ship only as a guard to demonstrate pooled (0.8899) ≠ average-of-averages (0.8786). Do not surface as the headline KPI. |

### A2. Availability by Asset Class vs Target (signed gap-to-target)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Availability Rate by Class` | `Availability Rate by Class = DIVIDE ( SUM ( fact_vehicle[AVAILABILITY_YTD] ), COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) ) ) )` | Light **0.9149**, Medium **0.8612**, Heavy **0.7948**, Off-Road **0.8882**, Other **0.9337** (`availability_by_class.*.availability_rate`) | Same pooled-mean measure as A1, sliced by asset class on the report. NULLs excluded. |
| `Class Target` | `Class Target = SELECTEDVALUE ( DimClassTarget[Target] )` ÷ 100 (or a lookup measure over a cited-targets table) | Light **95**, Medium **92**, Heavy **85**, Off-Road **88**, Other **90** (`availability_by_class.*.target`) | Audit-cited targets (AG 2019.AU2.2 / May 2023 FSD) — **cited, never recalculated.** Store as a small reference table, not hard-coded in a measure. |
| `Gap to Target` | `Gap to Target = [Availability Rate by Class] - DIVIDE ( [Class Target], 100 )` | Light **−0.0351**, Medium **−0.0588**, Heavy **−0.0552**, Off-Road **+0.0082**, Other **+0.0337** (`availability_by_class.*.gap_to_target`) | **Signed** (actual − target/100); negative = below benchmark (D-03). Light/Medium/Heavy are below target; Off-Road/Other clear it. |

### A3. Exception List — Critically-Low Units

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Below Target Unit Count` | `Below Target Unit Count = COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) && fact_vehicle[AVAILABILITY_YTD] < DIVIDE ( RELATED ( DimClassTarget[Target] ), 100 ) ) )` | **1,734** (rows in `exception_list.csv`) | One threshold rule (below class target, D-01). The named list itself is the `exception_list.csv` table rendered with `gap_to_target` ascending (worst first); the strict `<` excludes NULL availability. |

### A4. Underutilization Rate (overall / by using division / specialized)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Underutilization Rate` | `Underutilization Rate = DIVIDE ( CALCULATE ( COUNTROWS ( fact_vehicle ), fact_vehicle[Utilization] = "Underutilized" ), CALCULATE ( COUNTROWS ( fact_vehicle ), NOT ISBLANK ( fact_vehicle[Utilization] ) ) )` | **0.0572 ≈ 5.8%** (`overall_underutilization_rate` = 0.05721153846153846) | Computed over the **2,080** matched light-duty units (`Utilization` not blank). Classification is **pre-applied, never recomputed.** Slice by using division on the report. |
| `Light-Duty Matched Count` | `Light-Duty Matched Count = CALCULATE ( COUNTROWS ( fact_vehicle ), NOT ISBLANK ( fact_vehicle[Utilization] ) )` | **2,080** (`light_duty_matched_n`) | The availability⋈utilization join denominator (DQ report §7). |
| `Specialized Share` | `Specialized Share = DIVIDE ( CALCULATE ( COUNTROWS ( fact_vehicle ), fact_vehicle[specialized_units] = "Yes" ), CALCULATE ( COUNTROWS ( fact_vehicle ), NOT ISBLANK ( fact_vehicle[Utilization] ) ) )` | per-division in `underutilization_by_division.csv` (e.g. Facilities Mgmt 0.719) | Specialized-units share alongside underutilization, by using division. |

### A5. Disposal-Candidate Cross-Measure (SME screening list)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Disposal Candidate Count` | `Disposal Candidate Count = COUNTROWS ( FILTER ( fact_vehicle, NOT ISBLANK ( fact_vehicle[AVAILABILITY_YTD] ) && fact_vehicle[AVAILABILITY_YTD] < DIVIDE ( RELATED ( DimClassTarget[Target] ), 100 ) && fact_vehicle[Utilization] = "Underutilized" ) )` | **34** (`disposal_candidate = true` rows in `exception_list.csv`) | **SME screening list, NOT a disposal decision.** Below class target (D-01) **AND** pre-classified `Underutilized` (D-02). Same single threshold rule as A2/A3 — no second floor. Label the visual "screening list for SME review." |

---

## Ferry Operations (Domain B)

### B1. Lifetime / Period Totals (ALL data)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Lifetime Sales` | `Lifetime Sales = SUM ( fact_ferry[Sales Count] )` | **13,257,804** (`ferry_lifetime_sales`) | All 15-min intervals, full span May 2015 → Jun 2026 (D-09); partial years included for lifetime totals. |
| `Lifetime Redemptions` | `Lifetime Redemptions = SUM ( fact_ferry[Redemption Count] )` | **13,076,317** (`ferry_lifetime_redemptions`) | All data. |

### B2. Year-over-Year Trend (complete years 2016–2025 only)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Sales by Year` | `Sales by Year = CALCULATE ( SUM ( fact_ferry[Sales Count] ), dim_date[year] >= 2016 && dim_date[year] <= 2025 )` | 2019 **1,249,725**, 2020 **366,606** (`ferry_sales_2019` / `ferry_sales_2020`) | **YoY restricted to complete years 2016–2025** (D-10); partial 2015/2026 excluded so endpoints don't distort. |
| `Sales YoY Growth` | `Sales YoY Growth = DIVIDE ( [Sales by Year] - CALCULATE ( [Sales by Year], DATEADD ( dim_date[date], -1, YEAR ) ), CALCULATE ( [Sales by Year], DATEADD ( dim_date[date], -1, YEAR ) ) )` | full series in `ferry_yoy.csv` (2020 YoY **−0.7067**) | **2020 < 2019 COVID dip** is a locked guard (`tests/test_kpis.py`). `DIVIDE` guards the first-year null denominator. |

### B3. Seasonality Profile (pool all years by month)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Sales by Month (all years)` | `Sales by Month = CALCULATE ( SUM ( fact_ferry[Sales Count] ), ALLEXCEPT ( dim_date, dim_date[month] ) )` | profile in `data/kpi/ferry_seasonality` | Pools **every year by calendar month** (D-11) — **no annualization / partial-year estimation.** Reuse the Phase-2 `season` field; summer months peak. |

### B4. Day-of-Week × Hour-of-Day Heatmap (ALL data)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Sales by DoW x Hour` | `Sales by DoW x Hour = SUM ( fact_ferry[Sales Count] )` | long-form grid in `ferry_heatmap.csv` | Place `fact_ferry[day_of_week]` on rows × `dim_time[hour_of_day]` on columns (D-09, all data). Heatmap orientation is a Phase-4 presentation choice; reuse the Phase-2 `day_of_week` derivation. |

### B5. Sales-to-Redemption Gap (signed)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Sales-Redemption Gap` | `Sales-Redemption Gap = SUM ( fact_ferry[Sales Count] ) - SUM ( fact_ferry[Redemption Count] )` | 2016 **+92,649**, 2020 **−7,940** (`sales_redemption_gap.csv` `total_gap`) | **Signed** (`Sales − Redemption`, never `abs()`), reusing the Phase-2 `sales_redemption_gap` field. The sales-vs-redemption interpretation is **flagged for SME validation** (DQ report A3). |

### B6. Distribution Stats (right-skew story)

| Measure name | DAX | SQL validation value | Notes |
|--------------|-----|----------------------|-------|
| `Sales Max (per interval)` | `Sales Max = MAX ( fact_ferry[Sales Count] )` | **7,229** (`ferry_sales_max`) | Locked distribution guard (`ferry_sales_max == 7229`). |
| `Sales Median (per interval)` | `Sales Median = MEDIAN ( fact_ferry[Sales Count] )` | **12** (`ferry_sales_median`) | Median **12** vs max **7,229** = heavy right skew driven by real peak windows (summer weekends/holidays), **not a data error.** |

---

## Sources & Licence

- City of Toronto **Open Data** portal — the three source datasets.
- **May 2023 FSD** General Government Committee report.
- Auditor General **Operational Review 2019.AU2.2 / 2019.AU2.3**.
- Licence: **Open Government Licence – Toronto**.

*Every SQL validation value is transcribed from `data/kpi/kpi_values.json` or a `data/kpi/*.csv` table, computed by `src/fleet_analytics/kpis.py` and locked by `tests/test_kpis.py`. DAX is a text build contract — no `.pbix`/PBIP/TMDL is generated; the Power BI canvas is authored manually in Phase 4. Audit thresholds are cited, never recalculated.*
