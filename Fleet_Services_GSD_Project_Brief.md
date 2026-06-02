# Fleet Services Analytics — GSD Project Brief

**Purpose:** Seed document for `/gsd-new-project`. Paste/reference this when kicking off the GSD loop so research → requirements → roadmap start from a grounded vision rather than defaults.

**Architecture decision (already made):** Claude Code + GSD own the **data engineering layer** (ingest, clean, model, KPI logic, tested). The **Power BI report** is authored manually in Power BI Desktop on top of the modeled output. The GSD loop does **not** try to generate the `.pbix` canvas — it produces clean modeled tables, a KPI/measures spec, and a page-by-page report spec for hand-authoring.

---

## 1. Context

The City of Toronto's **Fleet Services Division (FSD)** manages the City's vehicle fleet and Toronto Island Ferry operations. The **Auditor General** audited FSD and issued recommendations to improve fleet maintenance efficiency and effectiveness. Two AG report themes anchor this work: **vehicle downtime** (2019.AU2.2, "Lengthy Downtime Requires Immediate Attention") and **underutilization** (2019.AU2.3, "Stronger Corporate Oversight Needed for Underutilized Vehicles").

You are the business analyst. Mandate: analyze three datasets, define meaningful KPIs and value-added measures, build a dashboard, and summarize findings + recommendations for management.

**Real stakeholders (from the FSD report to the General Government Committee, May 2023):** David Jollimore (General Manager, Fleet Services), Vukadin Lalovic (Director, Fleet Asset Management), Miguel Lamsaki (Acting Director, Fleet Maintenance). Client divisions (Toronto Water, Transportation Services, Parks & Recreation, Solid Waste, etc.) are the fleet consumers.

## 2. Deliverables (three required components + PDF)

1. **Requirements-gathering approach** — the steps taken to gather requirements that guided the analytics plan.
2. **Stakeholder engagement strategy** — how business stakeholders were engaged.
3. **Dashboard** — Power BI dashboard highlighting KPIs, trends, exceptions, and business insights, **plus a PDF export** of the dashboard.

Late submissions rejected. Pass mark 70% → panel interview with a 10-minute presentation of this work.

## 3. The data (real schemas — profiled from the supplied CSVs)

### 3a. City Vehicle Availability — 4,614 rows (one row per vehicle; cross-sectional, no date grain)
Key fields: `UNIT_NO` (zero-padded string), `AVAILABILITY_YTD` (0–1 fraction; mean ≈ 0.89; **209 nulls ≈ 4.5%**), `UNIT_TYPE` (asset class), `OWNER_DIVISION` (21 divisions), model `YEAR` (1982–2026), `IN_SERV_DT`, `SEASONAL` (375 seasonal), `STATUS_DESC` (4,195 Active), plus `MAKE`, `MODEL`, `CATEGORY`/`CAT_DESC`/`CATEGORY_CLASS`/`CAT_GRP`, `HIGH_PRIORITY`, `REF_DIVISION`.

`UNIT_TYPE` maps onto the audit's asset classes (with published availability targets):

| Asset class | Vehicles | Target | 2022 actual (audit) |
|---|---|---|---|
| Light Duty | 2,113 | 95% | 91% |
| Off-Road | 716 | 88% | 84% |
| Heavy Duty | 626 | 85% | 76% |
| Medium Duty | 611 | 92% | 83% |
| Other | 548 | 90% | 94% |

> Note: the portal lists this dataset as **Retired** — treat the supplied file as a point-in-time snapshot and state the pull date.

### 3b. Light-Duty Vehicle Utilization — 2,086 rows (one row per light-duty vehicle)
`UNIT_NO` (int), `Utilization` (**binary**: Not Underutilized 1,966 / Underutilized 120 ≈ **5.8%**), `Specialized units` (Yes 825 / No 1,261), `REF_USING_DIV` (20 divisions), plus `YEAR`, `MAKE`, `MODEL`.

> The underutilization classification is **pre-applied**. The km/engine-hour logic is not in the data — cite the audit definition: under 5,000 km or 125 engine hours and average usage under 3 days/week (where telematics exists). The audit reported ~14% underutilized (Mar 2023); the 5.8% here is a legitimate insight to surface (different period / fleet right-sizing since 2023).

### 3c. Toronto Island Ferry Ticket Counts — 272,529 rows (15-minute grain, May 2015 → Jun 2026, ~11 yrs)
`Timestamp`, `Sales Count` (tickets sold), `Redemption Count` (tickets scanned at boarding — assumed interpretation). Highly skewed (median 12, max 7,229 per 15-min window → strong seasonality). No nulls.

### 3d. Join model
Availability ⋈ Utilization on `UNIT_NO` (normalize: strip leading zeros / cast). **2,080 of 2,086** utilization records match availability. Ferry stands alone (separate domain). This join is the "value-added measurement" most candidates miss.

## 4. KPIs, measures & insights

**Domain A — Fleet Maintenance (availability ⋈ utilization)**
- Overall fleet availability rate (avg `AVAILABILITY_YTD`).
- **Availability by asset class vs. target** (flagship: actual vs. 95/92/85/88/90, plus gap-to-target).
- % of vehicles below an availability threshold; **exception list** of critically low / near-0% units (drill-through).
- Availability by owner division.
- Fleet age (derived from model YEAR / `IN_SERV_DT`) and **availability-vs-age trend**.
- Underutilization rate overall and **by using division** (flag divisions above fleet average).
- Specialized vs. non-specialized underutilization split.
- **Value-added cross-measure:** availability of underutilized vs. not-underutilized vehicles → disposal candidates (low availability *and* underutilized). Ties directly to the AG's downtime + underutilization themes and the audit's right-sizing narrative (143 assets removed, ~$411K avg annual maintenance saved).

**Domain B — Ferry Operations (time series)**
- Total tickets sold & redeemed (lifetime + period).
- YoY annual volume trend + growth rate (call out the 2020–21 dip explicitly).
- Seasonality: monthly and seasonal demand profile (summer peak).
- **Day-of-week × hour-of-day demand heatmap** → staffing/scheduling insight; identify peak 15-min windows.
- Sales-to-redemption gap over time (advance sales / no-shows / timing lag).
- Average daily volume by season; peak-day identification.

**Dashboard must surface:** KPIs (cards/targets), trends (age-vs-availability, ferry YoY/seasonal), exceptions (units below target, divisions above underutilization avg, ferry overload windows), insights (disposal candidates; ferry peak-staffing windows).

## 5. Proposed data model (star schema, Power BI friendly)

- **Fleet:** `dim_division` (lookup) + `fact_vehicle` (grain = UNIT_NO; because availability & utilization are 1:1 per vehicle, this doubles as the vehicle dimension — a single enriched table is idiomatic here). Attributes: asset_class, make, model, model_year, fleet_age_years, in_service_date, seasonal_flag, specialized_flag, status, high_priority. Measures: availability_ytd, utilization_status.
- **Ferry:** `fact_ferry` (grain = 15-min timestamp; measures sales_count, redemption_count, gap) + `dim_date` (year, quarter, month, day, day_of_week, is_weekend, season) + `dim_time` (hour, 15-min slot, daypart). Enables Power BI time intelligence.

## 6. Tech stack
Python + DuckDB for ETL (matches your portfolio), pandas where convenient, pytest for transformation/join-integrity tests, optional GitHub Actions CI. Output: clean Parquet/CSV for Power BI import. Optionally scaffold a PBIP/TMDL model so the semantic model + DAX are version-controlled even though the report canvas is authored in Desktop.

## 7. Phase roadmap (for the GSD loop)

- **Phase 1 — Ingest, profile & DQ baseline.** Load 3 CSVs to DuckDB; data dictionary + data-quality report (nulls, ranges, outliers, the 5.8% vs 14% discrepancy); documented assumptions. Tests: schema + row counts.
- **Phase 2 — Transform & model.** Handle 209 availability nulls; normalize `UNIT_NO`; parse timestamps; derive fleet_age, season, daypart, day_of_week, is_weekend, sales_redemption_gap; build the star-schema tables; join availability ⋈ utilization. Output Parquet/CSV. Tests: join integrity, derived-field correctness.
- **Phase 3 — KPI / measure layer.** Implement all KPIs as SQL/Python; validate availability-by-class against audit benchmarks; produce a **KPI definitions doc** (formulas) + a **DAX-ready measures spec** (copy-paste into Power BI). Tests: KPI bounds/sanity.
- **Phase 4 — Power BI delivery spec.** Page-by-page report spec — *Page 1 Fleet Maintenance*, *Page 2 Ferry Operations*, *Summary/Insights landing page*; slicer plan (asset class, division, season, date), theme, exact DAX, and the PDF-export layout. (You author from this in Desktop.)
- **Phase 5 — Narrative deliverables.** Draft (1) requirements-gathering approach and (2) stakeholder-engagement strategy, grounded in the AG audit + FSD report (sponsor = GM Fleet Services; SMEs = Directors; consumers = client divisions; oversight = Auditor General). Claude drafts; you refine.
- **Phase 6 — Ship.** Final dashboard PDF, README with screenshots, citations, repo cleanup; package all three components.

## 8. Assumptions to state explicitly
- Availability is a point-in-time YTD snapshot (dataset retired; record pull date).
- Underutilization is pre-classified; km/engine-hour thresholds cited from the audit, not recomputed.
- Ferry: Sales = sold, Redemption = boarded.
- 209 availability nulls excluded from rate calculations (document the choice).
- 5.8% underutilized (current) vs 14% (audit, Mar 2023) reflects period/fleet-size differences.

## 9. Sources to cite
- City of Toronto Open Data — City Vehicle Availability; Light-Duty Vehicle Utilization; Toronto Island Ferry Ticket Counts (open.toronto.ca).
- "Fleet Services' Report of the City of Toronto's Fleet Availability and Utilization Rates," General Government Committee, May 8 2023 (toronto.ca legislative docs) — KPI definitions, targets, thresholds, stakeholders.
- Auditor General Fleet Services Operational Review — Phase One (2019.AU2.2, 2019.AU2.3).
- Open Government Licence – Toronto.

---

## 10. Suggested `/gsd-new-project` kickoff prompt

> I'm building a fleet analytics project for a City of Toronto business-analyst assignment. Claude Code owns the data engineering layer only; the Power BI report is authored manually by me on top of the modeled output — do **not** attempt to generate a .pbix. Read the attached brief (`Fleet_Services_GSD_Project_Brief.md`) for context: three datasets (vehicle availability, light-duty utilization, ferry ticket counts), real schemas, the KPI set, the star-schema model, and a 6-phase roadmap. Ask me about: null-handling strategy, whether to scaffold PBIP/TMDL, and how much of the two narrative deliverables you should draft vs. outline. Then produce requirements + a roadmap that follows the phases in the brief.
